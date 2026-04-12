from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import Variant


def get_or_create_default_variant(db: Session, teacher_id: int) -> Variant:
    v = db.execute(
        select(Variant).where(Variant.teacher_id == teacher_id, Variant.slug == "default"),
    ).scalar_one_or_none()
    if v:
        return v
    v = Variant(teacher_id=teacher_id, name="По умолчанию", slug="default")
    db.add(v)
    db.flush()
    return v


def list_variants(db: Session, teacher_id: int) -> list[Variant]:
    return list(
        db.execute(select(Variant).where(Variant.teacher_id == teacher_id)).scalars().all(),
    )
