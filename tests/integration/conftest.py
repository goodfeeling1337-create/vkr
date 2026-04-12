"""Интеграционные тесты: поднимите БД (например `docker compose up -d db`) и выполните `alembic upgrade head`."""

from __future__ import annotations

import os

import pytest

_DEFAULT_URL = "postgresql+psycopg://dn_user:dn_pass@127.0.0.1:5432/dn_db"


@pytest.fixture(scope="module")
def integration_env() -> None:
    url = os.environ.get("INTEGRATION_DATABASE_URL") or os.environ.get("DATABASE_URL") or _DEFAULT_URL
    os.environ["DATABASE_URL"] = url
    from app.core.config import get_settings
    from app.db.session import reset_engine

    reset_engine()
    get_settings.cache_clear()
    try:
        from app.db.session import get_engine

        with get_engine().connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as exc:  # noqa: BLE001 — показать причину пропуска
        pytest.skip(f"PostgreSQL недоступен ({url}): {exc}")
    yield


@pytest.fixture(scope="module")
def client(integration_env: None):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
