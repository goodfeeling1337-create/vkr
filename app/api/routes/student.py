"""Студент: список работ, отправка попытки."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import require_student
from app.api.views import templates
from app.core.config import get_settings
from app.db.session import get_db
from app.models.orm import User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo
from app.services import attempt_service
from app.services.reference_access import SubmissionNotAllowed

router = APIRouter()


@router.get("/student", response_class=HTMLResponse)
async def student_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
) -> HTMLResponse:
    works = ref_repo.published_works_for_student(db, user.mentor_teacher_id)
    my_attempts = att_repo.list_attempts_for_student(db, user.id)
    return templates.TemplateResponse(
        request,
        "student_dashboard.html",
        {
            "user": user,
            "works": works,
            "attempts": my_attempts,
        },
    )


@router.post("/student/submit")
async def student_submit(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
    upload: UploadFile = File(...),
    reference_version_id: Optional[str] = Form(None),
) -> Response:
    data = await upload.read()
    rv = int(reference_version_id) if reference_version_id else None
    settings = get_settings()
    try:
        aid, _ = attempt_service.process_student_submission(
            db,
            student=user,
            file_bytes=data,
            original_filename=upload.filename or "work.xlsx",
            reference_version_id=rv,
            fallback_allow_optional_pure=settings.allow_optional_pure_junction_relations,
        )
    except SubmissionNotAllowed as e:
        works = ref_repo.published_works_for_student(db, user.mentor_teacher_id)
        my_attempts = att_repo.list_attempts_for_student(db, user.id)
        return templates.TemplateResponse(
            request,
            "student_dashboard.html",
            {
                "user": user,
                "works": works,
                "attempts": my_attempts,
                "error": str(e),
            },
            status_code=e.http_status,
        )
    except ValueError as e:
        works = ref_repo.published_works_for_student(db, user.mentor_teacher_id)
        my_attempts = att_repo.list_attempts_for_student(db, user.id)
        return templates.TemplateResponse(
            request,
            "student_dashboard.html",
            {
                "user": user,
                "works": works,
                "attempts": my_attempts,
                "error": str(e),
            },
            status_code=400,
        )
    return RedirectResponse(f"/student/attempt/{aid}", status_code=302)
