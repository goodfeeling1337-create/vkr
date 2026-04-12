from __future__ import annotations

import re
from dataclasses import dataclass

from app.checker.common.excel_io import get_cell_str

_SECTION_RE = re.compile(
    r"^\s*Задание\s*№?\s*(\d{1,2})\s*$",
    re.IGNORECASE | re.UNICODE,
)


@dataclass
class SectionHit:
    task_number: int
    row: int
    col: int


class SectionLocator:
    """
    Finds 'Задание №N' by scanning each cell (not whole-row concat).
    Ignores neighbor cells like 'Правильно'.
    """

    def __init__(self, matrix: list[list[object]], max_col_scan: int | None = None) -> None:
        self.matrix = matrix
        self.max_row = len(matrix)
        self.max_col = max_col_scan or (max(len(r) for r in matrix) if matrix else 0)

    def find_sections(self) -> dict[int, SectionHit]:
        hits: dict[int, SectionHit] = {}
        for r_idx, row in enumerate(self.matrix, start=1):
            limit = min(len(row), self.max_col)
            for c_idx in range(limit):
                cell = row[c_idx]
                s = get_cell_str(cell)
                if not s:
                    continue
                m = _SECTION_RE.match(s.strip())
                if not m:
                    continue
                n = int(m.group(1))
                if 1 <= n <= 13:
                    if n not in hits:
                        hits[n] = SectionHit(task_number=n, row=r_idx, col=c_idx + 1)
        return hits
