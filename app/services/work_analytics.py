"""Агрегаты по опубликованной работе (попытки, баллы, частые ошибки по заданиям)."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.orm import CheckRun, ReferenceWorkVersion, StudentAttempt


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

    wrong_by_task: Counter[int] = Counter()
    crs = db.scalars(select(CheckRun).join(StudentAttempt).where(StudentAttempt.reference_version_id.in_(vids))).all()
    for cr in crs[:500]:
        try:
            rep = json.loads(cr.report_json)
        except json.JSONDecodeError:
            continue
        tasks = rep.get("tasks") or {}
        for tn, tr in tasks.items():
            try:
                n = int(tn)
            except (TypeError, ValueError):
                continue
            if not isinstance(tr, dict):
                continue
            st = tr.get("status")
            if st and st != "correct":
                wrong_by_task[n] += 1
        if rep.get("workbook_structure_errors"):
            wrong_by_task[0] += 1

    return {
        "attempts_total": int(attempts_total or 0),
        "students_distinct": int(students_distinct or 0),
        "avg_score": float(avg_score) if avg_score is not None else None,
        "max_score_avg": float(max_score_avg) if max_score_avg is not None else None,
        "task_wrong_counts": {str(k): v for k, v in sorted(wrong_by_task.items())},
    }
