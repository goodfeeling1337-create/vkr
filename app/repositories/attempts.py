from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.orm import ReferenceWork, ReferenceWorkVersion, StudentAttempt, TeacherReview


def create_attempt(
    db: Session,
    *,
    student_id: int,
    reference_version_id: int,
    filename: str | None,
) -> StudentAttempt:
    a = StudentAttempt(
        student_id=student_id,
        reference_version_id=reference_version_id,
        submitted_filename=filename,
    )
    db.add(a)
    db.flush()
    return a


def get_attempt(db: Session, attempt_id: int) -> StudentAttempt | None:
    return db.get(StudentAttempt, attempt_id)


def get_attempt_detail(db: Session, attempt_id: int) -> StudentAttempt | None:
    return db.execute(
        select(StudentAttempt)
        .options(
            joinedload(StudentAttempt.student),
            joinedload(StudentAttempt.reference_version)
            .joinedload(ReferenceWorkVersion.reference_work)
            .joinedload(ReferenceWork.variant),
            joinedload(StudentAttempt.teacher_review).options(
                selectinload(TeacherReview.comments),
                selectinload(TeacherReview.files),
            ),
        )
        .where(StudentAttempt.id == attempt_id),
    ).unique().scalar_one_or_none()


def list_attempts_for_teacher(db: Session, teacher_id: int) -> list[StudentAttempt]:
    q = (
        select(StudentAttempt)
        .join(ReferenceWorkVersion, StudentAttempt.reference_version_id == ReferenceWorkVersion.id)
        .join(ReferenceWork, ReferenceWorkVersion.reference_work_id == ReferenceWork.id)
        .where(ReferenceWork.teacher_id == teacher_id)
        .options(joinedload(StudentAttempt.student))
        .order_by(StudentAttempt.id.desc())
    )
    return list(db.execute(q).scalars().unique().all())


def list_attempts_for_student(db: Session, student_id: int) -> list[StudentAttempt]:
    return list(
        db.execute(
            select(StudentAttempt)
            .where(StudentAttempt.student_id == student_id)
            .order_by(StudentAttempt.id.desc()),
        )
        .scalars()
        .all(),
    )
