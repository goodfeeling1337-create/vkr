"""
Веса автопроверяемых заданий и итоговый максимум.

По умолчанию бинарные задания = 1.0; ручные 10 и 12 = 0 в итоге автопроверки.
Расширение: разные веса для training/testing можно подставить через код/настройки позже.
"""

from __future__ import annotations

AUTO_CHECKED_TASKS = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13})
MANUAL_ONLY_TASKS = frozenset({10, 12})

# Явные веса (частичный балл в будущем — через TaskCheckResult + эти веса)
TASK_MAX_SCORE: dict[int, float] = {n: 1.0 for n in AUTO_CHECKED_TASKS}
for _m in MANUAL_ONLY_TASKS:
    TASK_MAX_SCORE[_m] = 0.0


def max_score_for_task(task_number: int) -> float:
    return float(TASK_MAX_SCORE.get(task_number, 1.0 if task_number in AUTO_CHECKED_TASKS else 0.0))


def total_max_score() -> float:
    return sum(max_score_for_task(t) for t in range(1, 14))
