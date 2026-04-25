from __future__ import annotations

import logging
from io import BytesIO

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.checker.reference_compiler import compile_reference_payloads, snapshot_json
from app.checker.timeout import CheckerTimeoutError, checker_timeout
from app.core.config import get_settings
from app.models.orm import ReferenceTaskAnswer, ReferenceWork, ReferenceWorkVersion
from app.services import file_storage

log = logging.getLogger(__name__)


def _create_version(
    db: Session,
    *,
    reference_work_id: int,
    version_number: int,
    file_bytes: bytes,
    original_filename: str,
) -> ReferenceWorkVersion:
    bio = BytesIO(file_bytes)
    wb = load_workbook(bio, data_only=True)
    settings = get_settings()
    try:
        with checker_timeout(settings.checker_timeout_seconds):
            payloads, errors = compile_reference_payloads(wb)
    except CheckerTimeoutError as e:
        raise ValueError(str(e)) from e
    if errors:
        log.warning("compile errors: %s", errors)
        raise ValueError("; ".join(errors))
    ver = ReferenceWorkVersion(
        reference_work_id=reference_work_id,
        version_number=version_number,
        original_filename=original_filename,
        storage_path="",  # заполняется после успешной загрузки файла
        compiled_snapshot_json=snapshot_json(payloads),
        template_metadata_json=None,
    )
    db.add(ver)
    db.flush()
    for tn, payload in payloads.items():
        db.add(
            ReferenceTaskAnswer(
                version_id=ver.id,
                task_number=tn,
                expected_payload=payload,
            ),
        )
    path = file_storage.store_upload(file_bytes, "ref", original_filename)
    ver.storage_path = str(path)
    return ver


def upload_new_reference(
    db: Session,
    *,
    teacher_id: int,
    scoring_mode: str,
    title: str,
    file_bytes: bytes,
    original_filename: str,
    publish: bool,
) -> ReferenceWorkVersion:
    settings = get_settings()
    if scoring_mode not in ("training", "testing"):
        scoring_mode = "training"
    rw = ReferenceWork(
        teacher_id=teacher_id,
        title=title,
        is_published=publish,
        scoring_mode=scoring_mode,
        allow_optional_pure_junction=settings.allow_optional_pure_junction_relations,
    )
    db.add(rw)
    db.flush()
    ver = _create_version(
        db,
        reference_work_id=rw.id,
        version_number=1,
        file_bytes=file_bytes,
        original_filename=original_filename,
    )
    db.commit()
    db.refresh(ver)
    log.info("Reference uploaded: work=%s version=%s", rw.id, ver.id)
    return ver


def increment_version_upload(
    db: Session,
    *,
    reference_work: ReferenceWork,
    file_bytes: bytes,
    original_filename: str,
) -> ReferenceWorkVersion:
    next_v = max((v.version_number for v in reference_work.versions), default=0) + 1
    ver = _create_version(
        db,
        reference_work_id=reference_work.id,
        version_number=next_v,
        file_bytes=file_bytes,
        original_filename=original_filename,
    )
    db.commit()
    db.refresh(ver)
    return ver
