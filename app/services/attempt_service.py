from __future__ import annotations

import json
import logging
from io import BytesIO
from typing import Optional

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.checker.engine import report_to_json, run_check
from app.checker.parse_only import parse_all_tasks
from app.models.orm import (
    CheckResultItem,
    CheckRun,
    ParsedAttemptSnapshot,
    StudentAttemptFile,
)
from app.repositories import reference as ref_repo
from app.repositories.attempts import create_attempt
from app.services import file_storage

log = logging.getLogger(__name__)


def process_student_submission(
    db: Session,
    *,
    student_id: int,
    file_bytes: bytes,
    original_filename: str,
    reference_version_id: Optional[int],
    fallback_allow_optional_pure: bool,
) -> tuple[int, int]:
    """
    Returns (attempt_id, check_run_id).
    reference_version_id required if metadata missing (caller validates).
    """
    bio = BytesIO(file_bytes)
    wb = load_workbook(bio, data_only=True)
    from app.checker.common.template_metadata_io import read_metadata_from_workbook

    meta = read_metadata_from_workbook(wb)
    if meta is not None:
        reference_version_id = meta.reference_version_id
    if reference_version_id is None:
        raise ValueError("Не удалось определить эталон: укажите версию эталона в форме")

    ver = ref_repo.get_version(db, reference_version_id)
    if ver is None:
        raise ValueError("Эталон не найден")

    rw = ver.reference_work
    allow_junction = rw.variant.allow_optional_pure_junction if rw and rw.variant else fallback_allow_optional_pure

    payloads = ref_repo.task_payloads_for_version(db, reference_version_id)
    # Deserialize json keys from DB - task numbers as int
    ref_payloads = {int(k): v for k, v in payloads.items()}

    report = run_check(
        wb,
        ref_payloads,
        allow_optional_pure_junction=allow_junction,
    )

    path = file_storage.store_upload(file_bytes, "attempt", original_filename)
    att = create_attempt(
        db,
        student_id=student_id,
        reference_version_id=reference_version_id,
        filename=original_filename,
    )
    db.add(
        StudentAttemptFile(
            attempt_id=att.id,
            kind="student_upload",
            storage_path=str(path),
            original_name=original_filename,
        ),
    )
    snap = parse_all_tasks(wb)
    db.add(
        ParsedAttemptSnapshot(
            attempt_id=att.id,
            snapshot_json=json.dumps(snap, ensure_ascii=False),
        ),
    )
    sm = rw.variant.scoring_mode if rw and rw.variant else "training"
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
    db.refresh(att)
    db.refresh(cr)
    log.info("Attempt %s checked run %s score %s/%s", att.id, cr.id, report.total_score, report.max_score)
    return att.id, cr.id
