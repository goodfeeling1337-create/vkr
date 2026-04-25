from __future__ import annotations

import logging
from io import BytesIO
from typing import Optional

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.checker.common.template_metadata_io import read_metadata_from_workbook
from app.checker.engine import report_to_json, run_check
from app.checker.timeout import CheckerTimeoutError, checker_timeout
from app.core.config import get_settings as _get_settings
from app.models.orm import (
    AttemptFileKind,
    CheckResultItem,
    CheckRun,
    StudentAttemptFile,
    User,
)
from app.repositories import reference as ref_repo
from app.repositories.attempts import create_attempt
from app.services import file_storage
from app.services.reference_access import ensure_student_may_submit_version
from app.services.submission_policy import validate_submission_allowed

log = logging.getLogger(__name__)


def process_student_submission(
    db: Session,
    *,
    student: User,
    file_bytes: bytes,
    original_filename: str,
    reference_version_id: Optional[int],
    fallback_allow_optional_pure: bool,
) -> tuple[int, int]:
    """
    Returns (attempt_id, check_run_id).
    Серверная проверка эталона: нельзя подставить чужой reference_version_id или id из подделанного metadata.
    """
    bio = BytesIO(file_bytes)
    wb = load_workbook(bio, data_only=True)

    mr = read_metadata_from_workbook(wb)
    meta = mr.metadata
    file_vid: int | None = meta.reference_version_id if meta is not None else None

    form_vid = reference_version_id
    if file_vid is not None and form_vid is not None and file_vid != form_vid:
        raise ValueError(
            "Версия эталона в файле не совпадает с выбранной в форме. "
            "Скачайте актуальный шаблон или выберите правильную версию.",
        )

    resolved_id = file_vid if file_vid is not None else form_vid
    if resolved_id is None:
        raise ValueError(
            "Не удалось определить, к какому эталону относится файл. Выберите эталон вручную в форме.",
        )

    if file_vid is not None:
        metadata_tag = mr.source  # hidden_sheet | hidden_cells
    else:
        metadata_tag = "manual_form"

    ver = ensure_student_may_submit_version(db, student, resolved_id)
    reference_version_id = ver.id

    validate_submission_allowed(db, student=student, ver=ver)

    rw = ver.reference_work
    allow_junction = (
        rw.allow_optional_pure_junction if rw is not None else fallback_allow_optional_pure
    )

    payloads = ref_repo.task_payloads_for_version(db, reference_version_id)
    ref_payloads = {int(k): v for k, v in payloads.items()}

    log.info(
        "student submission: user_id=%s version_id=%s metadata_source=%s",
        student.id,
        reference_version_id,
        metadata_tag,
    )

    _settings = _get_settings()
    try:
        with checker_timeout(_settings.checker_timeout_seconds):
            report = run_check(
                wb,
                ref_payloads,
                allow_optional_pure_junction=allow_junction,
                metadata_resolution=metadata_tag,
            )
    except CheckerTimeoutError as e:
        raise ValueError(str(e)) from e

    att = create_attempt(
        db,
        student_id=student.id,
        reference_version_id=reference_version_id,
        filename=original_filename,
    )
    sm = rw.scoring_mode if rw is not None else "training"
    cr = CheckRun(
        attempt_id=att.id,
        scoring_mode=sm,
        total_score=report.total_score,
        max_score=report.max_score,
        report_json=report_to_json(report),
    )
    db.add(cr)
    db.flush()
    for tn, tr in report.task_results.items():
        db.add(
            CheckResultItem(
                check_run_id=cr.id,
                task_number=tn,
                status=tr.status.value,
                score=tr.score,
                max_score=tr.max_score,
                detail_json={
                    "errors": tr.errors,
                    "warnings": tr.warnings,
                    "human_message": tr.human_message,
                    "parsed_answer": tr.parsed_answer,
                    "expected_answer_snapshot": tr.expected_answer_snapshot,
                },
            ),
        )
    db.commit()

    path = file_storage.store_upload(file_bytes, "attempt", original_filename)
    db.add(
        StudentAttemptFile(
            attempt_id=att.id,
            kind=AttemptFileKind.student_upload,
            storage_path=str(path),
            original_name=original_filename,
        ),
    )
    db.commit()
    db.refresh(att)
    db.refresh(cr)
    log.info("Attempt %s checked run %s score %s/%s", att.id, cr.id, report.total_score, report.max_score)
    return att.id, cr.id
