"""Агрегаты по опубликованной работе (попытки, баллы, частые ошибки по заданиям)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.orm import CheckResultItem, CheckRun, ReferenceWorkVersion, StudentAttempt


def analytics_for_reference_work(db: Session, reference_work_id: int) -> dict[str, Any]:
    vids = list(
        db.scalars(
            select(ReferenceWorkVersion.id).where(ReferenceWorkVersion.reference_work_id == reference_work_id),
        ).all(),
    )
    if not vids:
        return {
            "attempts_total": 0,
            "students_distinct": 0,
            "avg_score": None,
            "max_score_avg": None,
            "task_wrong_counts": {},
        }

    attempts_total = db.scalar(
        select(func.count()).select_from(StudentAttempt).where(StudentAttempt.reference_version_id.in_(vids)),
    )
    students_distinct = db.scalar(
        select(func.count(func.distinct(StudentAttempt.student_id))).where(
            StudentAttempt.reference_version_id.in_(vids),
        ),
    )
    avg_row = db.execute(
        select(func.avg(CheckRun.total_score), func.avg(CheckRun.max_score)).join(
            StudentAttempt,
            CheckRun.attempt_id == StudentAttempt.id,
        ).where(StudentAttempt.reference_version_id.in_(vids)),
    ).one()
    avg_score, max_score_avg = avg_row

    # NEW: count wrong statuses per task via check_result_items (replaces Python-loop JSON parsing)
    rows = db.execute(
        select(
            CheckResultItem.task_number,
            func.count().label("cnt"),
        )
        .join(CheckRun, CheckResultItem.check_run_id == CheckRun.id)
        .join(StudentAttempt, CheckRun.attempt_id == StudentAttempt.id)
        .where(
            StudentAttempt.reference_version_id.in_(vids),
            CheckResultItem.status != "correct",
        )
        .group_by(CheckResultItem.task_number)
    ).all()
    wrong_by_task = {str(r.task_number): r.cnt for r in rows}

    return {
        "attempts_total": int(attempts_total or 0),
        "students_distinct": int(students_distinct or 0),
        "avg_score": float(avg_score) if avg_score is not None else None,
        "max_score_avg": float(max_score_avg) if max_score_avg is not None else None,
        "task_wrong_counts": wrong_by_task,
    }
