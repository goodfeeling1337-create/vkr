from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.api.session import sign_user_id
from app.api.views import templates
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import verify_password
from app.db.session import get_db
from app.models.orm import User
from app.repositories.users import get_user_by_username

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(user: Optional[User] = Depends(get_current_user_optional)) -> RedirectResponse:
    if user is None:
        return RedirectResponse("/login", status_code=302)
    if user.role.name in ("teacher", "admin"):
        return RedirectResponse("/teacher", status_code=302)
    return RedirectResponse("/student", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
) -> Response:
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"user": None})


@router.post("/login")
@limiter.limit("10/minute")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    u = get_user_by_username(db, username)
    if not u or not verify_password(password, u.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "error": "Неверный логин или пароль"},
            status_code=401,
        )
    settings = get_settings()
    token = sign_user_id(u.id)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        max_age=settings.session_max_age,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )
    return resp


@router.get("/logout")
async def logout() -> RedirectResponse:
    settings = get_settings()
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(settings.session_cookie_name)
    return resp
