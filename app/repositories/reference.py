from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.orm import ReferenceTaskAnswer, ReferenceWork, ReferenceWorkVersion


def list_reference_works_for_teacher(db: Session, teacher_id: int) -> list[ReferenceWork]:
    return list(
        db.execute(
            select(ReferenceWork)
            .where(ReferenceWork.teacher_id == teacher_id)
            .options(joinedload(ReferenceWork.versions))
            .order_by(ReferenceWork.id.desc()),
        )
        .scalars()
        .unique()
        .all(),
    )


def get_reference_work(db: Session, work_id: int) -> ReferenceWork | None:
    return db.execute(
        select(ReferenceWork)
        .options(joinedload(ReferenceWork.versions))
        .where(ReferenceWork.id == work_id),
    ).unique().scalar_one_or_none()


def get_version(db: Session, version_id: int) -> ReferenceWorkVersion | None:
    return db.execute(
        select(ReferenceWorkVersion)
        .options(
            joinedload(ReferenceWorkVersion.task_answers),
            joinedload(ReferenceWorkVersion.reference_work).joinedload(ReferenceWork.variant),
        )
        .where(ReferenceWorkVersion.id == version_id),
    ).scalar_one_or_none()


def published_works_for_student(db: Session, mentor_teacher_id: int | None) -> list[ReferenceWork]:
    q = (
        select(ReferenceWork)
        .where(ReferenceWork.is_published.is_(True))
        .options(joinedload(ReferenceWork.versions))
    )
    if mentor_teacher_id is not None:
        q = q.where(ReferenceWork.teacher_id == mentor_teacher_id)
    return list(db.execute(q.order_by(ReferenceWork.id.desc())).scalars().unique().all())


def task_payloads_for_version(db: Session, version_id: int) -> dict[int, dict]:
    rows = db.execute(
        select(ReferenceTaskAnswer).where(ReferenceTaskAnswer.version_id == version_id),
    ).scalars().all()
    return {r.task_number: dict(r.expected_payload) for r in rows}
