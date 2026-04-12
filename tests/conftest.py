from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: требуется PostgreSQL и применённые миграции (alembic upgrade head)")

