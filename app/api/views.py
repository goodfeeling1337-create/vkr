"""Общие Jinja2 templates для веб-слоёв (избегаем циклических импортов с main)."""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from app.core.csrf import CSRF_COOKIE_NAME, CSRF_FIELD_NAME, generate_csrf_token

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["csrf_field_name"] = CSRF_FIELD_NAME


@pass_context
def csrf_token(context: object) -> str:
    request = context.get("request") if hasattr(context, "get") else None
    if request is not None:
        state_token = getattr(request.state, "csrf_token", None)
        if isinstance(state_token, str) and state_token:
            return state_token
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        if isinstance(cookie_token, str) and cookie_token:
            return cookie_token
    return generate_csrf_token()


templates.env.globals["csrf_token"] = csrf_token
