"""Панель преподавателя: сводка по работам и попыткам."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
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
) -> HTMLResponse:
    works = ref_repo.list_reference_works_for_teacher(db, user.id)
    attempts = att_repo.list_attempts_for_teacher(db, user.id)
    return templates.TemplateResponse(
        request,
        "teacher_dashboard.html",
        {
            "user": user,
            "works": works,
            "attempts": attempts,
        },
    )
