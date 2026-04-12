from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_attribute_name, normalize_cell_value
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

_STAR = re.compile(r"\*+\s*$")


def parse_task3(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    if not rows:
        return ParseOutcome.failure("Пустая секция задания 3")
    rel_name = ""
    hi = 0
    first = rows[0]
    filled = [normalize_attribute_name(str(c)) for c in first if c and str(c).strip()]
    if len(filled) == 1 and "," not in (first[0] or ""):
        rel_name = filled[0]
        hi = 1
    headers_raw: list[str] = []
    key_attrs: set[str] = set()
    start_data = 0
    found = False
    for i in range(hi, len(rows)):
        raw_cells = [str(c) if c is not None else "" for c in rows[i]]
        if sum(1 for x in raw_cells if x.strip()) < 2:
            continue
        headers_raw = []
        key_attrs = set()
        for c in rows[i]:
            if not c:
                headers_raw.append("")
                continue
            s = str(c)
            is_key = bool(_STAR.search(s))
            name = normalize_attribute_name(_STAR.sub("", s))
            headers_raw.append(name)
            if is_key and name:
                key_attrs.add(name)
        start_data = i + 1
        found = True
        break
    if not found:
        return ParseOutcome.failure("Не найдена строка заголовков 1НФ (или нет ключевых пометок *)")
    headers = [normalize_attribute_name(h) for h in headers_raw if normalize_attribute_name(h)]
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
