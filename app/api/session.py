from __future__ import annotations

from typing import Optional

from itsdangerous import BadSignature, URLSafeSerializer

from app.core.config import get_settings


def _serializer() -> URLSafeSerializer:
    s = get_settings()
    return URLSafeSerializer(s.secret_key, salt="dn-user-session")


def sign_user_id(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id})


def unsign_user_id(token: str) -> Optional[int]:
    try:
        data = _serializer().loads(token)
        return int(data["uid"])
    except (BadSignature, KeyError, TypeError, ValueError):
        return None
