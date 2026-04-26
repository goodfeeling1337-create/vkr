from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_attribute_name, normalize_cell_value
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

_STAR = re.compile(r"\*+\s*$")


def _try_parse_header_row(row: list[object]) -> tuple[list[str], set[str]] | None:
    raw_cells = [str(c) if c is not None else "" for c in row]
    if sum(1 for x in raw_cells if x.strip()) < 2:
        return None
    headers_raw: list[str] = []
    key_attrs: set[str] = set()
    for c in row:
        if not c:
            headers_raw.append("")
            continue
        s = str(c)
        is_key = bool(_STAR.search(s))
        name = normalize_attribute_name(_STAR.sub("", s))
        headers_raw.append(name)
        if is_key and name:
            key_attrs.add(name)
    if not key_attrs:
        return None
    return headers_raw, key_attrs


def parse_task3(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    if not rows:
        return ParseOutcome.failure("Пустая секция задания 3")

    rel_name = ""
    start_scan = 0
    first = rows[0]
    filled = [normalize_attribute_name(str(c)) for c in first if c and str(c).strip()]

    # Сразу строка заголовков (без отдельной строки с названием отношения)
    hdr_try = _try_parse_header_row(first)
    if hdr_try is not None:
        headers_raw, key_attrs = hdr_try
        start_data = 1
    else:
        # Строка названия отношения: одна короткая ячейка без запятых
        if len(filled) == 1 and "," not in (first[0] or ""):
            rel_name = filled[0]
            start_scan = 1
        else:
            start_scan = 0

        headers_raw = []
        key_attrs = set()
        start_data = 0
        found = False
        for i in range(start_scan, len(rows)):
            parsed = _try_parse_header_row(rows[i])
            if parsed is None:
                continue
            headers_raw, key_attrs = parsed
            start_data = i + 1
            found = True
            break
        if not found:
            return ParseOutcome.failure(
                "Не найдена строка заголовков 1НФ (или нет ключевых пометок *)",
            )

    # Сохраняем длину и позиции столбцов как в headers_raw — иначе при пустой ячейке
    # в начале/конце строки заголовков «сжатый» список имён не совпадает с шириной строк
    # данных, и индексы ключа в check_task3 указывают не на те столбцы (ложные дубликаты).
    headers = [
        normalize_attribute_name(str(h)) if h is not None and str(h).strip() else ""
        for h in headers_raw
    ]
    data_rows: list[tuple[str, ...]] = []
    for i in range(start_data, len(rows)):
        r = rows[i]
        vals: list[str] = []
        for j in range(len(headers_raw)):
            v = r[j] if j < len(r) else None
            vals.append(normalize_cell_value(v))
        if all(not x for x in vals):
            continue
        data_rows.append(tuple(vals))
    out = {
        "relation": rel_name,
        "headers": headers,
        "key_attributes": sorted(key_attrs),
        "rows": data_rows,
    }
    return ParseOutcome.success(out)
