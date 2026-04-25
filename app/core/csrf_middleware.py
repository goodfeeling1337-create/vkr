"""CSRF middleware: проверяет токен для всех state-changing запросов."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_FIELD_NAME,
    generate_csrf_token,
    validate_csrf_token,
)

_EXEMPT_PATHS: set[str] = set()
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        if validate_csrf_token(cookie_token):
            request.state.csrf_token = cookie_token
        else:
            request.state.csrf_token = generate_csrf_token()

        if request.method in _SAFE_METHODS:
            response = await call_next(request)
            self._set_csrf_cookie(request, response)
            return response

        if request.url.path not in _EXEMPT_PATHS:
            form_token: str | None = None
            try:
                form = await request.form()
                form_token = form.get(CSRF_FIELD_NAME)
            except Exception:  # noqa: BLE001
                pass
            if not form_token:
                form_token = request.headers.get("X-CSRF-Token")
            if (
                not validate_csrf_token(form_token)
                or not validate_csrf_token(cookie_token)
                or form_token != cookie_token
            ):
                return JSONResponse(
                    {"detail": "CSRF-токен недействителен или отсутствует."},
                    status_code=403,
                )

        response = await call_next(request)
        self._set_csrf_cookie(request, response)
        return response

    @staticmethod
    def _set_csrf_cookie(request: Request, response: Response) -> None:
        current = request.cookies.get(CSRF_COOKIE_NAME)
        desired = getattr(request.state, "csrf_token", None)
        if desired and current != desired:
            settings = get_settings()
            response.set_cookie(
                CSRF_COOKIE_NAME,
                desired,
                httponly=False,
                samesite="lax",
                secure=settings.session_cookie_secure,
            )
