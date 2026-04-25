from __future__ import annotations

from app.core import auth_bruteforce as guard


def setup_function() -> None:
    guard._STATE.clear()


def test_lockout_after_repeated_failures(monkeypatch) -> None:
    t = 1000.0
    monkeypatch.setattr(guard, "_now", lambda: t)

    for _ in range(4):
        assert guard.record_failed_login("user", "127.0.0.1") == 0
    retry_after = guard.record_failed_login("user", "127.0.0.1")

    assert retry_after > 0
    assert guard.get_retry_after_seconds("user", "127.0.0.1") > 0


def test_clear_resets_block_state(monkeypatch) -> None:
    t = 2000.0
    monkeypatch.setattr(guard, "_now", lambda: t)
    for _ in range(5):
        guard.record_failed_login("user", "127.0.0.1")
    assert guard.get_retry_after_seconds("user", "127.0.0.1") > 0

    guard.clear_failed_logins("user", "127.0.0.1")

    assert guard.get_retry_after_seconds("user", "127.0.0.1") == 0
