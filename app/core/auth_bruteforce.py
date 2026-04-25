from __future__ import annotations

import threading
import time

_LOCK = threading.Lock()
_WINDOW_SECONDS = 300
_BLOCK_SECONDS = 300
_MAX_FAILURES = 5
_STATE: dict[tuple[str, str], dict[str, float | int]] = {}


def _now() -> float:
    return time.monotonic()


def _key(username: str, ip: str) -> tuple[str, str]:
    return (username.strip().lower(), ip)


def _prune(now: float) -> None:
    for key in list(_STATE.keys()):
        item = _STATE[key]
        blocked_until = float(item.get("blocked_until", 0))
        last_failure = float(item.get("last_failure", 0))
        if blocked_until <= now and (now - last_failure) > _WINDOW_SECONDS:
            _STATE.pop(key, None)


def get_retry_after_seconds(username: str, ip: str) -> int:
    now = _now()
    with _LOCK:
        _prune(now)
        item = _STATE.get(_key(username, ip))
        if not item:
            return 0
        blocked_until = float(item.get("blocked_until", 0))
        if blocked_until <= now:
            return 0
        return int(blocked_until - now) + 1


def record_failed_login(username: str, ip: str) -> int:
    now = _now()
    with _LOCK:
        _prune(now)
        key = _key(username, ip)
        item = _STATE.get(key) or {"count": 0, "last_failure": 0.0, "blocked_until": 0.0}
        last_failure = float(item.get("last_failure", 0.0))
        if now - last_failure > _WINDOW_SECONDS:
            item["count"] = 0
        item["count"] = int(item.get("count", 0)) + 1
        item["last_failure"] = now
        if int(item["count"]) >= _MAX_FAILURES:
            item["blocked_until"] = now + _BLOCK_SECONDS
        _STATE[key] = item
        blocked_until = float(item.get("blocked_until", 0))
        if blocked_until > now:
            return int(blocked_until - now) + 1
        return 0


def clear_failed_logins(username: str, ip: str) -> None:
    with _LOCK:
        _STATE.pop(_key(username, ip), None)
