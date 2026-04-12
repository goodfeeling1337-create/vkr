from __future__ import annotations

from typing import Any

from app.checker.common.excel_io import get_cell_str
from app.checker.common.section_locator import SectionLocator, SectionHit
from app.domain.workbook import ParsedTaskSection, ParsedWorkbook


def _trim_empty_tail(rows: list[list[str | None]]) -> list[list[str | None]]:
    while rows and all(v is None or v == "" for v in rows[-1]):
        rows.pop()
    return rows


def build_parsed_workbook(matrix: list[list[Any]]) -> ParsedWorkbook:
    loc = SectionLocator(matrix)
    hits = loc.find_sections()
    ordered = sorted(hits.items(), key=lambda x: (x[1].row, x[1].col))
    sections: dict[int, ParsedTaskSection] = {}
    for i, (task_num, hit) in enumerate(ordered):
        start = hit.row  # 1-based row of header
        if i + 1 < len(ordered):
            end_row = ordered[i + 1][1].row - 1
        else:
            end_row = len(matrix)
        body_start = start + 1
        rows: list[list[str | None]] = []
        raw_rows: list[tuple[int, list[Any]]] = []
        for r in range(body_start, end_row + 1):
            if r - 1 >= len(matrix):
                break
            raw = matrix[r - 1]
            raw_rows.append((r, list(raw)))
            norm_row: list[str | None] = []
            for cell in raw:
                s = get_cell_str(cell)
                if s is None:
                    norm_row.append(None)
                else:
                    t = s.strip()
                    norm_row.append(t if t else None)
            rows.append(norm_row)
        rows = _trim_empty_tail(rows)
        sections[task_num] = ParsedTaskSection(
            task_number=task_num,
            start_row=start,
            end_row=end_row,
            rows=rows,
            raw_rows=raw_rows,
        )
    return ParsedWorkbook(sections=sections)
