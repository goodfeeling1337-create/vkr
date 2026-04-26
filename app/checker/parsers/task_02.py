from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_attribute_name, normalize_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

_GROUP_HEAD = re.compile(r"^\s*группа\s*\d*\s*:?\s*$", re.IGNORECASE)


def parse_task2(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    groups: list[set[str]] = []
    current: set[str] | None = None
    for row in rows:
        cells = [str(c).strip() for c in row if c and str(c).strip()]
        if not cells:
            continue
        line = " ".join(cells)
        if _GROUP_HEAD.match(line) or re.match(r"^\s*\d+[\).]\s+", line):
            if current is not None and current:
                groups.append(current)
            current = set()
            continue
        if current is None:
            current = set()
        # Каждая ячейка — отдельный атрибут (плюс запятые/; внутри ячейки). Склейка через
        # пробел давала одну «суперстроку» и ломала сравнение с эталоном в нескольких ячейках.
        for cell in cells:
            na_cell = normalize_attribute_name(cell)
            # Подпись столбца «Ответ:» в отдельной ячейке — не атрибут отношения.
            if not na_cell or normalize_text(cell).lower().rstrip(":.;") in ("ответ", "ответ:"):
                continue
            for a in _split_attrs(cell):
                if a:
                    current.add(normalize_attribute_name(a))
    if current is not None and current:
        groups.append(current)
    if not groups:
        # fallback: whole section as one group from comma-separated lines
        g: set[str] = set()
        for row in rows:
            for c in row:
                if not c:
                    continue
                g.update(normalize_attribute_name(x) for x in re.split(r"[,;]", str(c)) if x.strip())
        if g:
            groups = [g]
    if not groups:
        return ParseOutcome.failure("Не удалось выделить повторяющиеся группы атрибутов")
    serial = [sorted(list(s)) for s in groups]
    serial_sorted = sorted(serial)
    return ParseOutcome.success({"groups": serial_sorted})


def _split_attrs(line: str) -> list[str]:
    import re as _re

    parts = _re.split(r"[,;]", line)
    return [p.strip() for p in parts if p.strip()]
