from __future__ import annotations

from typing import Any

from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection


def parse_raw_section(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    cells: list[str] = []
    for row in rows:
        for c in row:
            if c is not None and str(c).strip():
                cells.append(str(c))
    return ParseOutcome.success({"raw": "\n".join(cells)})
