"""Эталонные работы преподавателя: загрузка и карточка работы."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.api.views import templates
from app.db.session import get_db
from app.models.orm import User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo
from app.repositories.variants import get_or_create_variant_for_scoring_mode
from app.services import reference_service
from app.services.file_storage import read_upload_with_size_limit
from app.services.work_analytics import analytics_for_reference_work

log = logging.getLogger(__name__)

router = APIRouter()


def _render_upload_error(
    request: Request,
    db: Session,
    user: User,
    message: str,
    *,
    status: int = 400,
) -> Response:
    works = ref_repo.list_reference_works_for_teacher(db, user.id)
    attempts = att_repo.list_attempts_for_teacher(db, user.id)
    return templates.TemplateResponse(
        request,
        "teacher_dashboard.html",
        {
            "user": user,
            "works": works,
            "attempts": attempts,
            "error": message,
        },
        status_code=status,
    )


@router.post("/teacher/reference/upload")
async def teacher_upload_reference(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    title: str = Form(...),
    upload: UploadFile = File(...),
    publish: Optional[str] = Form(None),
    scoring_mode: Literal["training", "testing"] = Form("training"),
) -> Response:
    try:
        data = await read_upload_with_size_limit(upload, label="эталон")
    except ValueError as e:
        return _render_upload_error(request, db, user, str(e))
    v = get_or_create_variant_for_scoring_mode(db, user.id, scoring_mode)
    try:
        reference_service.upload_new_reference(
            db,
            teacher_id=user.id,
            variant_id=v.id,
            title=title,
            file_bytes=data,
            original_filename=upload.filename or "reference.xlsx",
            publish=publish == "on",
        )
    except ValueError as e:
        log.warning("upload failed: %s", e)
        return _render_upload_error(request, db, user, str(e))
    return RedirectResponse("/teacher", status_code=302)


@router.get("/teacher/reference/{work_id}", response_class=HTMLResponse)
async def teacher_reference_detail(
    request: Request,
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> HTMLResponse:
    w = ref_repo.get_reference_work(db, work_id)
    if not w or w.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    analytics = analytics_for_reference_work(db, work_id)
    return templates.TemplateResponse(
        request,
        "reference_detail.html",
        {
            "user": user,
            "work": w,
            "analytics": analytics,
        },
    )


@router.post("/teacher/reference/{work_id}/settings")
async def teacher_reference_settings(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    max_attempts: Optional[str] = Form(None),
    deadline_at: Optional[str] = Form(None),
) -> RedirectResponse:
    w = ref_repo.get_reference_work(db, work_id)
    if not w or w.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if max_attempts is not None and str(max_attempts).strip() != "":
        try:
            ma = int(max_attempts)
            w.max_attempts = max(1, ma)
        except ValueError:
            w.max_attempts = None
    else:
        w.max_attempts = None

    if deadline_at and str(deadline_at).strip():
        raw = str(deadline_at).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(raw)
            w.deadline_at = dt.replace(tzinfo=None) if dt.tzinfo else dt
        except ValueError:
            pass
    else:
        w.deadline_at = None
    db.commit()
    return RedirectResponse(f"/teacher/reference/{work_id}", status_code=302)


@router.post("/teacher/reference/{work_id}/publish")
async def teacher_reference_toggle_publish(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> RedirectResponse:
    w = ref_repo.get_reference_work(db, work_id)
    if not w or w.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    w.is_published = not w.is_published
    db.commit()
    return RedirectResponse(f"/teacher/reference/{work_id}", status_code=302)
