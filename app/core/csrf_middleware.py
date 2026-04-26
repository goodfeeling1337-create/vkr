"""CSRF middleware: проверяет токен для всех state-changing запросов."""
from __future__ import annotations

from urllib.parse import parse_qs

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_FIELD_NAME,
    generate_csrf_token,
    validate_csrf_token,
)

# POST /login: CSRF не проверяем (см. OWASP: низкий приоритет относительно CSRF после входа).
_EXEMPT_PATHS: frozenset[str] = frozenset({"/login"})
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _is_multipart(request: Request) -> bool:
    """Multipart нельзя читать в middleware до FastAPI File()/Form() — иначе 422 на upload."""
    ct = (request.headers.get("content-type") or "").lower()
    return "multipart/form-data" in ct


def _is_urlencoded(request: Request) -> bool:
    ct = (request.headers.get("content-type") or "").lower()
    return "application/x-www-form-urlencoded" in ct


async def _csrf_token_from_request(request: Request) -> str | None:
    """
    Извлекает CSRF-токен без request.form(): при BaseHTTPMiddleware form() потребляет
    поток без кеша _body, и внутреннее приложение получает пустое тело (422 на Form(...)).
    """
    hdr = request.headers.get("X-CSRF-Token")
    if hdr:
        return hdr
    if _is_multipart(request):
        return None
    if _is_urlencoded(request):
        raw = await request.body()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None
        vals = parse_qs(text, keep_blank_values=True).get(CSRF_FIELD_NAME)
        return vals[0] if vals else None
    return None


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.method in _SAFE_METHODS:
            response = await call_next(request)
            self._set_csrf_cookie(request, response)
            return response

        if request.url.path not in _EXEMPT_PATHS:
            if _is_multipart(request):
                # Не читаем тело; CSRF для multipart не проверяем (SameSite=Lax на cookie сессии).
                pass
            else:
                token = await _csrf_token_from_request(request)
                if not validate_csrf_token(token):
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
