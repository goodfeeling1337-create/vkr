from __future__ import annotations

import pytest

pytest.importorskip("slowapi")

from app.main import app


def test_app_import_smoke() -> None:
    assert app is not None


def test_required_routers_are_registered() -> None:
    routes = app.router.routes
    route_paths = {getattr(r, "path", "") for r in routes}
    assert "/login" in route_paths
    assert "/teacher" in route_paths
    assert "/student" in route_paths
    assert "/download/template/{version_id}" in route_paths
    assert "/teacher/reference/upload" in route_paths
    assert "/teacher/attempt/{attempt_id}" in route_paths
    assert "/student/attempt/{attempt_id}" in route_paths


def test_attempt_view_routes_not_duplicated() -> None:
    routes = app.router.routes
    method_paths = []
    for r in routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        if not path or not methods:
            continue
        for m in methods:
            method_paths.append((m, path))
    # Only one handler per method/path pair for attempt views.
    assert method_paths.count(("GET", "/student/attempt/{attempt_id}")) == 1
    assert method_paths.count(("GET", "/teacher/attempt/{attempt_id}")) == 1
