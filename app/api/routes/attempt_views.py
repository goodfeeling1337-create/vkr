"""Просмотр попытки: преподаватель и студент (страница с отчётом автопроверки)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_student, require_teacher
from app.api.views import templates
from app.db.session import get_db
from app.models.orm import CheckRun, User
from app.repositories import attempts as att_repo
from app.training_hints import CODE_TRAINING_HINTS, TASK_TRAINING_HINTS

router = APIRouter()


@router.get("/teacher/attempt/{attempt_id}", response_class=HTMLResponse)
async def teacher_attempt(
    request: Request,
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> HTMLResponse:
    att = att_repo.get_attempt_detail(db, attempt_id)
    if att is None:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    rw = att.reference_version.reference_work
    if rw.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    cr = db.execute(
        select(CheckRun).where(CheckRun.attempt_id == att.id).order_by(CheckRun.id.desc()),
    ).scalar_one_or_none()
    report = json.loads(cr.report_json) if cr else {}
    scoring_mode = rw.variant.scoring_mode if rw.variant else "training"
    return templates.TemplateResponse(
        request,
        "attempt_detail.html",
        {
            "user": user,
            "attempt": att,
            "report": report,
            "role": "teacher",
            "scoring_mode": scoring_mode,
            "training_task_hints": TASK_TRAINING_HINTS,
            "code_training_hints": CODE_TRAINING_HINTS,
        },
    )


@router.get("/student/attempt/{attempt_id}", response_class=HTMLResponse)
async def student_attempt_view(
    request: Request,
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
) -> HTMLResponse:
    att = att_repo.get_attempt_detail(db, attempt_id)
    if att is None or att.student_id != user.id:
        raise HTTPException(status_code=403, detail="У вас нет доступа к этой попытке")
    cr = db.execute(
        select(CheckRun).where(CheckRun.attempt_id == att.id).order_by(CheckRun.id.desc()),
    ).scalar_one_or_none()
    report = json.loads(cr.report_json) if cr else {}
    rw = att.reference_version.reference_work
    scoring_mode = rw.variant.scoring_mode if rw.variant else "training"
    return templates.TemplateResponse(
        request,
        "attempt_detail.html",
        {
            "user": user,
            "attempt": att,
            "report": report,
            "role": "student",
            "scoring_mode": scoring_mode,
            "training_task_hints": TASK_TRAINING_HINTS,
            "code_training_hints": CODE_TRAINING_HINTS,
        },
    )
