"""Проверка преподавателем: комментарии и файлы к попытке."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.db.session import get_db
from app.models.orm import User
from app.repositories import attempts as att_repo
from app.services import review_service
from app.services.file_storage import read_upload_with_size_limit

router = APIRouter()


@router.post("/teacher/attempt/{attempt_id}/comment")
async def teacher_comment(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    body: str = Form(...),
) -> RedirectResponse:
    att = att_repo.get_attempt(db, attempt_id)
    if att is None or att.reference_version.reference_work.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    try:
        review_service.add_comment(db, attempt_id, user.id, body)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Нет доступа") from None
    return RedirectResponse(f"/teacher/attempt/{attempt_id}", status_code=302)


@router.post("/teacher/attempt/{attempt_id}/review_file")
async def teacher_review_file(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    upload: UploadFile = File(...),
) -> RedirectResponse:
    att = att_repo.get_attempt(db, attempt_id)
    if att is None or att.reference_version.reference_work.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    try:
        data = await read_upload_with_size_limit(upload, label="файл проверки")
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    try:
        review_service.attach_review_file(db, attempt_id, user.id, data, upload.filename or "review.xlsx")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Нет доступа") from None
    return RedirectResponse(f"/teacher/attempt/{attempt_id}", status_code=302)
