"""Простая CSRF-защита через signed double-submit cookie."""
from __future__ import annotations

import secrets

from itsdangerous import BadSignature, URLSafeSerializer

from app.core.config import get_settings

CSRF_COOKIE_NAME = "dn_csrf"
CSRF_FIELD_NAME = "_csrf_token"


def _csrf_serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().secret_key, salt="dn-csrf")


def generate_csrf_token() -> str:
    """Генерирует подписанный CSRF-токен."""
    raw = secrets.token_hex(16)
    return _csrf_serializer().dumps(raw)


def validate_csrf_token(token: str | None) -> bool:
    """Проверяет CSRF-токен. False = невалидный или отсутствует."""
    if not token:
        return False
    try:
        _csrf_serializer().loads(token)
        return True
    except BadSignature:
        return False
