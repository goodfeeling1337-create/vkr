"""Эталонные работы преподавателя: загрузка и карточка работы."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.api.views import templates
from app.db.session import get_db
from app.models.orm import User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo
from app.repositories.variants import get_or_create_default_variant
from app.services import reference_service

log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/teacher/reference/upload")
async def teacher_upload_reference(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    title: str = Form(...),
    upload: UploadFile = File(...),
    publish: Optional[str] = Form(None),
) -> Response:
    data = await upload.read()
    v = get_or_create_default_variant(db, user.id)
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
        works = ref_repo.list_reference_works_for_teacher(db, user.id)
        attempts = att_repo.list_attempts_for_teacher(db, user.id)
        return templates.TemplateResponse(
            request,
            "teacher_dashboard.html",
            {
                "user": user,
                "works": works,
                "attempts": attempts,
                "error": str(e),
            },
            status_code=400,
        )
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
    return templates.TemplateResponse(request, "reference_detail.html", {"user": user, "work": w})
