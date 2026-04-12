from __future__ import annotations

from dataclasses import dataclass

AUTO_CHECKED_TASKS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13})
MANUAL_ONLY_TASKS = frozenset({10, 12})


def max_score_for_task(task_number: int) -> float:
    if task_number in MANUAL_ONLY_TASKS:
        return 0.0
    return 1.0


def total_max_score() -> float:
    return sum(max_score_for_task(t) for t in range(1, 14))
