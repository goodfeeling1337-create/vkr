from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user_optional, require_login, require_student, require_teacher
from app.api.session import sign_user_id
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.security import verify_password
from app.db.seed import seed_if_empty
from app.db.session import SessionLocal, get_db
from app.models.orm import CheckRun, TeacherReview, TeacherReviewFile, User
from app.repositories import attempts as att_repo
from app.repositories import reference as ref_repo
from app.repositories.users import get_user_by_username
from app.repositories.variants import get_or_create_default_variant
from app.services import attempt_service, reference_service, review_service, template_service

setup_logging()
log = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app = FastAPI(title="DB Normalization Checker")

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def _startup() -> None:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def index(user: Optional[User] = Depends(get_current_user_optional)) -> RedirectResponse:
    if user is None:
        return RedirectResponse("/login", status_code=302)
    if user.role.name in ("teacher", "admin"):
        return RedirectResponse("/teacher", status_code=302)
    return RedirectResponse("/student", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
) -> Response:
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@app.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    u = get_user_by_username(db, username)
    if not u or not verify_password(password, u.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "user": None, "error": "Неверный логин или пароль"},
            status_code=401,
        )
    settings = get_settings()
    token = sign_user_id(u.id)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(settings.session_cookie_name, token, httponly=True, max_age=settings.session_max_age)
    return resp


@app.get("/logout")
async def logout() -> RedirectResponse:
    settings = get_settings()
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(settings.session_cookie_name)
    return resp


@app.get("/teacher", response_class=HTMLResponse)
async def teacher_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> HTMLResponse:
    works = ref_repo.list_reference_works_for_teacher(db, user.id)
    attempts = att_repo.list_attempts_for_teacher(db, user.id)
    return templates.TemplateResponse(
        "teacher_dashboard.html",
        {"request": request, "user": user, "works": works, "attempts": attempts},
    )


@app.post("/teacher/reference/upload")
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
            "teacher_dashboard.html",
            {
                "request": request,
                "user": user,
                "works": works,
                "attempts": attempts,
                "error": str(e),
            },
            status_code=400,
        )
    return RedirectResponse("/teacher", status_code=302)


@app.get("/teacher/reference/{work_id}", response_class=HTMLResponse)
async def teacher_reference_detail(
    request: Request,
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> HTMLResponse:
    w = ref_repo.get_reference_work(db, work_id)
    if not w or w.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    return templates.TemplateResponse("reference_detail.html", {"request": request, "user": user, "work": w})


@app.get("/download/template/{version_id}")
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


@app.get("/teacher/attempt/{attempt_id}", response_class=HTMLResponse)
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
    return templates.TemplateResponse(
        "attempt_detail.html",
        {
            "request": request,
            "user": user,
            "attempt": att,
            "report": report,
            "role": "teacher",
        },
    )


@app.post("/teacher/attempt/{attempt_id}/comment")
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


@app.post("/teacher/attempt/{attempt_id}/review_file")
async def teacher_review_file(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    upload: UploadFile = File(...),
) -> RedirectResponse:
    att = att_repo.get_attempt(db, attempt_id)
    if att is None or att.reference_version.reference_work.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    data = await upload.read()
    try:
        review_service.attach_review_file(db, attempt_id, user.id, data, upload.filename or "review.xlsx")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Нет доступа") from None
    return RedirectResponse(f"/teacher/attempt/{attempt_id}", status_code=302)


@app.get("/student", response_class=HTMLResponse)
async def student_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
) -> HTMLResponse:
    works = ref_repo.published_works_for_student(db, user.mentor_teacher_id)
    my_attempts = att_repo.list_attempts_for_student(db, user.id)
    return templates.TemplateResponse(
        "student_dashboard.html",
        {
            "request": request,
            "user": user,
            "works": works,
            "attempts": my_attempts,
        },
    )


@app.post("/student/submit")
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
            student_id=user.id,
            file_bytes=data,
            original_filename=upload.filename or "work.xlsx",
            reference_version_id=rv,
            fallback_allow_optional_pure=settings.allow_optional_pure_junction_relations,
        )
    except ValueError as e:
        works = ref_repo.published_works_for_student(db, user.mentor_teacher_id)
        my_attempts = att_repo.list_attempts_for_student(db, user.id)
        return templates.TemplateResponse(
            "student_dashboard.html",
            {
                "request": request,
                "user": user,
                "works": works,
                "attempts": my_attempts,
                "error": str(e),
            },
            status_code=400,
        )
    return RedirectResponse(f"/student/attempt/{aid}", status_code=302)


@app.get("/student/attempt/{attempt_id}", response_class=HTMLResponse)
async def student_attempt_view(
    request: Request,
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
) -> HTMLResponse:
    att = att_repo.get_attempt_detail(db, attempt_id)
    if att is None or att.student_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    cr = db.execute(
        select(CheckRun).where(CheckRun.attempt_id == att.id).order_by(CheckRun.id.desc()),
    ).scalar_one_or_none()
    report = json.loads(cr.report_json) if cr else {}
    return templates.TemplateResponse(
        "attempt_detail.html",
        {"request": request, "user": user, "attempt": att, "report": report, "role": "student"},
    )


@app.get("/download/review/{file_id}")
async def download_review_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
) -> FileResponse:
    f = db.execute(
        select(TeacherReviewFile)
        .options(joinedload(TeacherReviewFile.review).joinedload(TeacherReview.attempt))
        .where(TeacherReviewFile.id == file_id),
    ).scalar_one_or_none()
    if f is None:
        raise HTTPException(status_code=404, detail="Файл не найден")
    att = f.review.attempt
    if user.role.name == "student" and att.student_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if user.role.name == "teacher" and att.reference_version.reference_work.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    return FileResponse(f.storage_path, filename=f.original_name)
