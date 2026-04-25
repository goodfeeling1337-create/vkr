"""CSRF middleware: проверяет токен для всех state-changing запросов."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_FIELD_NAME,
    generate_csrf_token,
    validate_csrf_token,
)

# POST /login: нельзя вызывать request.form() до роутера — иначе тело часто не доходит
# до Form(...) и в браузере появляется 422 (missing username/password).
# Login CSRF здесь сознательно не проверяем (см. OWASP: низкий приоритет относительно CSRF после входа).
_EXEMPT_PATHS: frozenset[str] = frozenset({"/login"})
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
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
            if not validate_csrf_token(form_token):
                return JSONResponse(
                    {"detail": "CSRF-токен недействителен или отсутствует."},
                    status_code=403,
                )

        response = await call_next(request)
        self._set_csrf_cookie(request, response)
        return response

    @staticmethod
    def _set_csrf_cookie(request: Request, response: Response) -> None:
        if CSRF_COOKIE_NAME not in request.cookies:
            token = generate_csrf_token()
            response.set_cookie(
                CSRF_COOKIE_NAME,
                token,
                httponly=False,
                samesite="lax",
                secure=False,
            )
