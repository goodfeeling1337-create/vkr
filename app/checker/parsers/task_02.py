from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_attribute_name, normalize_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

_GROUP_HEAD = re.compile(r"^\s*группа\s*\d*\s*:?\s*$", re.IGNORECASE)
_LABEL_CELLS = frozenset({"ответ", "ответ:", "answer"})


def _is_label_cell(cell: str) -> bool:
    return normalize_attribute_name(cell).lower().rstrip(":.;") in _LABEL_CELLS


def _cells_to_attrs(cells: list[str]) -> set[str]:
    result: set[str] = set()
    for cell in cells:
        if not cell or _is_label_cell(cell):
            continue
        for a in _split_attrs(cell):
            n = normalize_attribute_name(a)
            if n:
                result.add(n)
    return result


def parse_task2(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    groups: list[set[str]] = []
    current: set[str] | None = None
    has_explicit_headers = False

    for row in rows:
        cells = [str(c).strip() for c in row if c and str(c).strip()]
        if not cells:
            continue
        line = " ".join(cells)
        if _GROUP_HEAD.match(line) or re.match(r"^\s*\d+[\).]\s+", line):
            has_explicit_headers = True
            if current is not None and current:
                groups.append(current)
            current = set()
            continue
        if current is None:
            current = set()
        current.update(_cells_to_attrs(cells))

    if current is not None and current:
        groups.append(current)

    # Если нет явных заголовков групп и строки содержат несколько ячеек — каждая строка
    # является отдельной группой (формат эталона: атрибуты группы — в ячейках одной строки).
    if not has_explicit_headers and len(groups) <= 1:
        candidate = _parse_rows_as_groups(rows)
        if len(candidate) > 1:
            groups = candidate

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


def _parse_rows_as_groups(rows: list[list]) -> list[set[str]]:
    """Каждая строка с несколькими ячейками — отдельная группа."""
    result: list[set[str]] = []
    for row in rows:
        cells = [str(c).strip() for c in row if c and str(c).strip()]
        if not cells:
            continue
        line = " ".join(cells)
        if _GROUP_HEAD.match(line) or _is_label_cell(line):
            continue
        g = _cells_to_attrs(cells)
        if g:
            result.append(g)
    return result


def _split_attrs(line: str) -> list[str]:
    import re as _re

    parts = _re.split(r"[,;]", line)
    return [p.strip() for p in parts if p.strip()]
