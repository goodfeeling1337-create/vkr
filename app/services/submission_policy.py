"""Правила сдачи: дедлайн и лимит попыток по работе."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.orm import ReferenceWorkVersion, User
from app.repositories import attempts as att_repo


def validate_submission_allowed(
    db: Session,
    *,
    student: User,
    ver: ReferenceWorkVersion,
) -> None:
    rw = ver.reference_work
    if rw.deadline_at:
        dl = rw.deadline_at
        if getattr(dl, "tzinfo", None) is not None:
            dl = dl.replace(tzinfo=None)
        if datetime.utcnow() > dl:
            raise ValueError("Срок сдачи по этой работе истёк.")
    n = att_repo.count_attempts_for_student_on_work(db, student.id, rw.id)
    if rw.max_attempts is not None and n >= rw.max_attempts:
        raise ValueError(
            f"Достигнут лимит попыток для этой работы ({rw.max_attempts}).",
        )
