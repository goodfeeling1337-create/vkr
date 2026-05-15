"""Панель преподавателя: сводка по работам и попыткам."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.api.views import templates
from app.db.session import get_db
from app.models.orm import User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo

router = APIRouter()


@router.get("/teacher", response_class=HTMLResponse)
async def teacher_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    course: Optional[str] = Query(None, description="Фильтр по метке курса"),
    work_id: Optional[int] = Query(None, description="Фильтр по работе (тесту)"),
) -> HTMLResponse:
    is_admin = user.role.name == "admin"
    course_f = (course or "").strip() or None
    if is_admin:
        works = ref_repo.list_all_reference_works(db)
        attempts = att_repo.list_attempts_all(
            db,
            course_label=course_f,
            reference_work_id=work_id,
        )
        course_labels = ref_repo.distinct_course_labels_all(db)
    else:
        works = ref_repo.list_reference_works_for_teacher(db, user.id)
        attempts = att_repo.list_attempts_for_teacher(
            db,
            user.id,
            course_label=course_f,
            reference_work_id=work_id,
        )
        course_labels = ref_repo.distinct_course_labels_for_teacher(db, user.id)
    return templates.TemplateResponse(
        request,
        "teacher_dashboard.html",
        {
            "user": user,
            "works": works,
            "attempts": attempts,
            "course_labels": course_labels,
            "filter_course": course_f,
            "filter_work_id": work_id,
            "is_admin": is_admin,
        },
    )
