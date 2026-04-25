"""Утилиты для ограничения времени выполнения checker pipeline."""
from __future__ import annotations

import signal
import sys
from contextlib import contextmanager
from typing import Generator


class CheckerTimeoutError(Exception):
    """Проверка превысила допустимое время выполнения."""
    pass


@contextmanager
def checker_timeout(seconds: int) -> Generator[None, None, None]:
    """
    Контекстный менеджер: прерывает выполнение через `seconds` секунд.
    Работает только в main thread (Unix). При seconds=0 — без ограничений.
    На Windows всегда пропускает без ограничений.
    """
    if seconds <= 0 or sys.platform == "win32":
        yield
        return

    def _handler(signum: int, frame: object) -> None:
        raise CheckerTimeoutError(
            f"Проверка прервана: превышен лимит времени ({seconds} сек). "
            "Возможно, файл содержит слишком много данных."
        )

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
