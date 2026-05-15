"""Панель администратора: обзор системы (не смешивается с ежедневной проверкой преподавателя)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.api.views import templates
from app.db.session import get_db
from app.models.orm import User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo
from app.repositories import users as users_repo

router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> HTMLResponse:
    users = users_repo.list_users(db)
    works = ref_repo.list_all_reference_works(db)
    attempts = att_repo.list_attempts_all(db, limit=80)
    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {
            "user": user,
            "users": users,
            "works": works,
            "attempts": attempts,
        },
    )
