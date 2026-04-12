from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedTaskSection:
    """Raw-ish content for one assignment block."""

    task_number: int
    start_row: int
    end_row: int
    # 2D list of normalized cell strings (trimmed); None for empty
    rows: list[list[str | None]] = field(default_factory=list)
    raw_rows: list[tuple[int, list[Any]]] = field(default_factory=list)


@dataclass
class ParsedWorkbook:
    sections: dict[int, ParsedTaskSection] = field(default_factory=dict)
    sheet_title: str | None = None
