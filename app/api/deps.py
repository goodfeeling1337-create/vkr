from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.session import unsign_user_id
from app.core.config import get_settings
from app.db.session import get_db
from app.models.orm import User
from app.repositories.users import get_user


def get_current_user_optional(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    uid = unsign_user_id(token)
    if uid is None:
        return None
    return get_user(db, uid)


def redirect_login() -> None:
    raise HTTPException(
        status_code=status.HTTP_302_FOUND,
        detail="Требуется вход",
        headers={"Location": "/login"},
    )


def require_login(user: Annotated[Optional[User], Depends(get_current_user_optional)]) -> User:
    if user is None:
        redirect_login()
    return user


def require_teacher(user: Annotated[User, Depends(require_login)]) -> User:
    if user.role.name not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Нужна роль преподавателя")
    return user


def require_student(user: Annotated[User, Depends(require_login)]) -> User:
    if user.role.name not in ("student", "admin"):
        raise HTTPException(status_code=403, detail="Нужна роль студента")
    return user
