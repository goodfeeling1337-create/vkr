"""Смоук-тесты HTTP: логин и панель преподавателя."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_login_page_ok(client) -> None:
    r = client.get("/login")
    assert r.status_code == 200
    assert "login" in r.text.lower() or "логин" in r.text.lower()


def test_teacher_login_and_dashboard(client) -> None:
    r = client.post(
        "/login",
        data={"username": "teacher", "password": "teacher"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    r2 = client.get("/teacher", follow_redirects=False)
    assert r2.status_code == 200


def test_anonymous_root_redirects_to_login(client) -> None:
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location") == "/login"
