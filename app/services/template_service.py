from __future__ import annotations

import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.metadata import TemplateMetadata
from app.repositories.reference import get_version
from app.services.template_builder import build_student_template

log = logging.getLogger(__name__)


def materialize_student_template(db: Session, reference_version_id: int) -> tuple[Path, str]:
    ver = get_version(db, reference_version_id)
    if ver is None:
        raise ValueError("Версия эталона не найдена")
    rw = ver.reference_work
    meta = TemplateMetadata(
        template_id=str(uuid.uuid4()),
        template_version=1,
        variant_id=None,
        reference_work_id=rw.id,
        reference_version_id=ver.id,
    )
    src = Path(ver.storage_path)
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.upload_dir / f"template_{uuid.uuid4().hex}.xlsx"
    build_student_template(src, dest, meta)
    fname = f"template_{rw.title}_v{ver.version_number}.xlsx"
    return dest, fname
