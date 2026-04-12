from __future__ import annotations

import logging
from io import BytesIO

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.checker.reference_compiler import compile_reference_payloads, snapshot_json
from app.models.orm import ReferenceTaskAnswer, ReferenceWork, ReferenceWorkVersion
from app.services import file_storage

log = logging.getLogger(__name__)


def upload_new_reference(
    db: Session,
    *,
    teacher_id: int,
    variant_id: int,
    title: str,
    file_bytes: bytes,
    original_filename: str,
    publish: bool,
) -> ReferenceWorkVersion:
    bio = BytesIO(file_bytes)
    wb = load_workbook(bio, data_only=True)
    payloads, errors = compile_reference_payloads(wb)
    if errors:
        log.warning("compile errors: %s", errors)
        # still allow save if partial? Strict: fail
        raise ValueError("; ".join(errors))
    path = file_storage.store_upload(file_bytes, "ref", original_filename)
    rw = ReferenceWork(
        teacher_id=teacher_id,
        variant_id=variant_id,
        title=title,
        is_published=publish,
    )
    db.add(rw)
    db.flush()
    ver = ReferenceWorkVersion(
        reference_work_id=rw.id,
        version_number=1,
        original_filename=original_filename,
        storage_path=str(path),
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
    bio = BytesIO(file_bytes)
    wb = load_workbook(bio, data_only=True)
    payloads, errors = compile_reference_payloads(wb)
    if errors:
        raise ValueError("; ".join(errors))
    path = file_storage.store_upload(file_bytes, "ref", original_filename)
    next_v = max((v.version_number for v in reference_work.versions), default=0) + 1
    ver = ReferenceWorkVersion(
        reference_work_id=reference_work.id,
        version_number=next_v,
        original_filename=original_filename,
        storage_path=str(path),
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
    db.commit()
    db.refresh(ver)
    return ver
