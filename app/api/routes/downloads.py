from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_login
from app.db.session import get_db
from app.models.orm import TeacherReview, TeacherReviewFile, User
from app.repositories import reference as ref_repo
from app.services import template_service

router = APIRouter()


@router.get("/download/template/{version_id}")
async def download_template(
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
) -> FileResponse:
    ver = ref_repo.get_version(db, version_id)
    if ver is None:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    rw = ver.reference_work
    if user.role.name == "student":
        if not rw.is_published:
            raise HTTPException(status_code=403, detail="Не опубликовано")
        if user.mentor_teacher_id is not None and rw.teacher_id != user.mentor_teacher_id:
            raise HTTPException(status_code=403, detail="Нет доступа")
    elif user.role.name == "teacher" and rw.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    path, fname = template_service.materialize_student_template(db, version_id)
    return FileResponse(
        path,
        filename=fname,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/download/review/{file_id}")
async def download_review_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
) -> FileResponse:
    f = db.execute(
        select(TeacherReviewFile)
        .options(joinedload(TeacherReviewFile.review).joinedload(TeacherReview.attempt))
        .where(TeacherReviewFile.id == file_id),
    ).unique().scalar_one_or_none()
    if f is None:
        raise HTTPException(status_code=404, detail="Файл не найден")
    att = f.review.attempt
    if user.role.name == "student" and att.student_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if user.role.name == "teacher" and att.reference_version.reference_work.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    return FileResponse(f.storage_path, filename=f.original_name)
