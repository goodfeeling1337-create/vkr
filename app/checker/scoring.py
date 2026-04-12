"""Обратная совместимость: веса вынесены в app.core.scoring_config."""

from __future__ import annotations

from app.core.scoring_config import (  # noqa: F401
    AUTO_CHECKED_TASKS,
    MANUAL_ONLY_TASKS,
    max_score_for_task,
    total_max_score,
)
