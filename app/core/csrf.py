"""Простая CSRF-защита через signed double-submit cookie."""
from __future__ import annotations

import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings

CSRF_COOKIE_NAME = "dn_csrf"
CSRF_FIELD_NAME = "_csrf_token"


def _csrf_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt="dn-csrf")


def generate_csrf_token() -> str:
    """Генерирует подписанный CSRF-токен."""
    raw = secrets.token_hex(16)
    return _csrf_serializer().dumps(raw)


def validate_csrf_token(token: str | None) -> bool:
    """Проверяет CSRF-токен. False = невалидный или отсутствует."""
    if not token:
        return False
    try:
        _csrf_serializer().loads(token, max_age=get_settings().session_max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
