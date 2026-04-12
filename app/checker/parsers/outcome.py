from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class ParseOutcome(Generic[T]):
    ok: bool
    value: T | None
    error: str | None = None

    @classmethod
    def success(cls, v: T) -> ParseOutcome[T]:
        return cls(True, v, None)

    @classmethod
    def failure(cls, msg: str) -> ParseOutcome[T]:
        return cls(False, None, msg)
