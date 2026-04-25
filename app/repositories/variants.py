from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import Variant


def get_or_create_variant_for_scoring_mode(db: Session, teacher_id: int, scoring_mode: str) -> Variant:
    """
    Один «служебный» вариант на режим на преподавателя (slug mode-training / mode-testing).
    Название работы задаётся на эталоне (ReferenceWork.title), а не именем Variant.
    """
    if scoring_mode not in ("training", "testing"):
        scoring_mode = "training"
    slug = "mode-training" if scoring_mode == "training" else "mode-testing"
    v = db.execute(
        select(Variant).where(Variant.teacher_id == teacher_id, Variant.slug == slug),
    ).scalar_one_or_none()
    if v:
        if v.scoring_mode != scoring_mode:
            v.scoring_mode = scoring_mode
            db.flush()
        return v
    label = "Тренировка" if scoring_mode == "training" else "Тестирование"
    v = Variant(teacher_id=teacher_id, name=label, slug=slug, scoring_mode=scoring_mode)
    db.add(v)
    db.flush()
    return v
