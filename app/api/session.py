from __future__ import annotations

from typing import Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings


def _serializer() -> URLSafeTimedSerializer:
    s = get_settings()
    return URLSafeTimedSerializer(s.secret_key, salt="dn-user-session")


def sign_user_id(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id})


def unsign_user_id(token: str) -> Optional[int]:
    s = get_settings()
    try:
        data = _serializer().loads(token, max_age=s.session_max_age)
        return int(data["uid"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None
