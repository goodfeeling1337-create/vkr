from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import Variant


def _slug_base(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower(), flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-")[:56]
    return s or "variant"


def create_variant(
    db: Session,
    *,
    teacher_id: int,
    name: str,
    scoring_mode: str,
) -> Variant:
    base = _slug_base(name)
    slug = base
    n = 0
    while db.execute(select(Variant.id).where(Variant.teacher_id == teacher_id, Variant.slug == slug)).scalar_one_or_none():
        n += 1
        slug = f"{base}-{n}"
    v = Variant(teacher_id=teacher_id, name=name, slug=slug, scoring_mode=scoring_mode)
    db.add(v)
    db.flush()
    return v


def get_variant_for_teacher(db: Session, variant_id: int, teacher_id: int) -> Variant | None:
    v = db.get(Variant, variant_id)
    if v is None or v.teacher_id != teacher_id:
        return None
    return v


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
