"""Студент: список работ, отправка попытки."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import require_student
from app.api.views import templates
from app.core.config import get_settings
from app.db.session import get_db
from app.models.orm import ReferenceWork, User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo
from app.services import attempt_service
from app.services.file_storage import read_upload_with_size_limit
from app.services.reference_access import SubmissionNotAllowed
from app.services.submission_policy import validate_submission_allowed

router = APIRouter()


def _ensure_xlsx_filename(filename: str | None) -> str:
    name = (filename or "").strip()
    if not name or not name.lower().endswith(".xlsx"):
        raise ValueError("Нужно загрузить файл формата .xlsx")
    return name


def _handle_submission_error(
    request: Request,
    exc: Exception,
    template_name: str,
    ctx: dict[str, Any],
    status_code: int,
) -> Response:
    ctx["error"] = str(exc)
    return templates.TemplateResponse(request, template_name, ctx, status_code=status_code)


def _student_dashboard_context(db: Session, user: User) -> dict:
    works = ref_repo.published_works_for_student(db, user.mentor_teacher_id)
    my_attempts = att_repo.list_attempts_for_student(db, user.id)
    training = [w for w in works if w.scoring_mode == "training"]
    testing = [w for w in works if w.scoring_mode == "testing"]
    other = [w for w in works if w.scoring_mode not in ("training", "testing")]
    return {
        "user": user,
        "works": works,
        "works_training": training + other,
        "works_testing": testing,
        "attempts": my_attempts,
        "attempt_counts": att_repo.count_attempts_per_work(db, user.id),
    }


def _student_work_context(
    db: Session,
    user: User,
    work: ReferenceWork,
    *,
    error: str | None = None,
) -> dict[str, Any]:
    attempts = att_repo.list_attempts_for_student_on_work(db, user.id, work.id)
    best_score: float | None = None
    best_max: float | None = None
    attempt_rows: list[dict[str, Any]] = []
    for a in attempts:
        ts, ms = att_repo.latest_check_run_score(a)
        if ts is not None and (best_score is None or ts > best_score):
            best_score = ts
            best_max = ms
        attempt_rows.append({"attempt": a, "score": ts, "max_score": ms})
    ver = work.latest_version
    can_submit = True
    submit_block_reason: str | None = None
    if ver is None:
        can_submit = False
        submit_block_reason = "У работы нет загруженной версии эталона."
    else:
        try:
            validate_submission_allowed(db, student=user, ver=ver)
        except ValueError as e:
            can_submit = False
            submit_block_reason = str(e)
    scoring_mode = work.scoring_mode
    teacher_comments: list[dict[str, Any]] = []
    for a in attempts:
        rev = a.teacher_review
        if not rev:
            continue
        for c in rev.comments:
            teacher_comments.append(
                {"body": c.body, "at": c.created_at, "attempt_id": a.id},
            )
    teacher_comments.sort(key=lambda x: x["at"], reverse=True)
    return {
        "user": user,
        "work": work,
        "attempts": attempts,
        "attempt_rows": attempt_rows,
        "best_score": best_score,
        "best_max": best_max,
        "latest_attempt": attempts[0] if attempts else None,
        "can_submit": can_submit,
        "submit_block_reason": submit_block_reason,
        "scoring_mode": scoring_mode,
        "reference_version_id": ver.id if ver else None,
        "teacher_comments": teacher_comments,
        "error": error,
    }


@router.get("/student/work/{work_id}", response_class=HTMLResponse)
async def student_work_detail(
    request: Request,
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
) -> HTMLResponse:
    w = ref_repo.get_published_work_for_student(db, work_id, user.mentor_teacher_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Работа не найдена или недоступна")
    return templates.TemplateResponse(
        request,
        "student_work.html",
        _student_work_context(db, user, w),
    )


@router.post("/student/work/{work_id}/submit")
async def student_submit_for_work(
    request: Request,
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
    upload: UploadFile = File(...),
) -> Response:
    w = ref_repo.get_published_work_for_student(db, work_id, user.mentor_teacher_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Работа не найдена или недоступна")
    ver = w.latest_version
    settings = get_settings()
    ref_vid = ver.id if ver else None
    try:
        valid_name = _ensure_xlsx_filename(upload.filename)
        data = await read_upload_with_size_limit(upload, label="работа студента")
        aid, _ = attempt_service.process_student_submission(
            db,
            student=user,
            file_bytes=data,
            original_filename=valid_name,
            reference_version_id=ref_vid,
            fallback_allow_optional_pure=settings.allow_optional_pure_junction_relations,
        )
    except SubmissionNotAllowed as e:
        return _handle_submission_error(request, e, "student_work.html", _student_work_context(db, user, w), e.http_status)
    except ValueError as e:
        return _handle_submission_error(request, e, "student_work.html", _student_work_context(db, user, w), 400)
    return RedirectResponse(f"/student/attempt/{aid}", status_code=302)


@router.get("/student", response_class=HTMLResponse)
async def student_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "student_dashboard.html",
        _student_dashboard_context(db, user),
    )


@router.post("/student/submit")
async def student_submit(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
    upload: UploadFile = File(...),
    reference_version_id: Optional[str] = Form(None),
) -> Response:
    rv: int | None = None
    if reference_version_id and reference_version_id.strip():
        try:
            rv = int(reference_version_id.strip())
        except ValueError:
            rv = None
    settings = get_settings()
    try:
        valid_name = _ensure_xlsx_filename(upload.filename)
        data = await read_upload_with_size_limit(upload, label="работа студента")
        aid, _ = attempt_service.process_student_submission(
            db,
            student=user,
            file_bytes=data,
            original_filename=valid_name,
            reference_version_id=rv,
            fallback_allow_optional_pure=settings.allow_optional_pure_junction_relations,
        )
    except SubmissionNotAllowed as e:
        return _handle_submission_error(request, e, "student_dashboard.html", _student_dashboard_context(db, user), e.http_status)
    except ValueError as e:
        return _handle_submission_error(request, e, "student_dashboard.html", _student_dashboard_context(db, user), 400)
    return RedirectResponse(f"/student/attempt/{aid}", status_code=302)
