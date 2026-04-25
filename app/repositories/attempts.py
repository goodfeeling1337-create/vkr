from __future__ import annotations

from sqlalchemy import func, select
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
            .options(
                joinedload(StudentAttempt.reference_version)
                .joinedload(ReferenceWorkVersion.reference_work)
                .joinedload(ReferenceWork.variant),
            )
            .order_by(StudentAttempt.id.desc()),
        )
        .scalars()
        .unique()
        .all(),
    )


def list_attempts_for_student_on_work(
    db: Session,
    student_id: int,
    reference_work_id: int,
) -> list[StudentAttempt]:
    return list(
        db.execute(
            select(StudentAttempt)
            .join(ReferenceWorkVersion, StudentAttempt.reference_version_id == ReferenceWorkVersion.id)
            .where(
                StudentAttempt.student_id == student_id,
                ReferenceWorkVersion.reference_work_id == reference_work_id,
            )
            .options(
                joinedload(StudentAttempt.check_runs),
                joinedload(StudentAttempt.teacher_review).options(
                    selectinload(TeacherReview.comments),
                    selectinload(TeacherReview.files),
                ),
            )
            .order_by(StudentAttempt.id.desc()),
        )
        .scalars()
        .unique()
        .all(),
    )


def latest_check_run_score(attempt: StudentAttempt) -> tuple[float | None, float | None]:
    """Последний автопроверочный прогон: (total_score, max_score)."""
    runs = sorted(attempt.check_runs, key=lambda r: r.id, reverse=True)
    if not runs:
        return None, None
    cr = runs[0]
    return cr.total_score, cr.max_score


def count_attempts_per_work(db: Session, student_id: int) -> dict[int, int]:
    """Количество попыток по каждой работе для студента (все версии)."""
    rows = db.execute(
        select(ReferenceWorkVersion.reference_work_id, func.count().label("cnt"))
        .join(StudentAttempt, StudentAttempt.reference_version_id == ReferenceWorkVersion.id)
        .where(StudentAttempt.student_id == student_id)
        .group_by(ReferenceWorkVersion.reference_work_id),
    ).all()
    return {r.reference_work_id: r.cnt for r in rows}


def count_attempts_for_student_on_work(db: Session, student_id: int, reference_work_id: int) -> int:
    """Все попытки по любой версии данной работы."""
    n = db.scalar(
        select(func.count())
        .select_from(StudentAttempt)
        .join(ReferenceWorkVersion, StudentAttempt.reference_version_id == ReferenceWorkVersion.id)
        .where(
            StudentAttempt.student_id == student_id,
            ReferenceWorkVersion.reference_work_id == reference_work_id,
        ),
    )
    return int(n or 0)
