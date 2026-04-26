from __future__ import annotations

from typing import Any

from app.checker.normalizers import (
    normalize_attribute_name,
    normalize_cell_value,
    normalize_text,
)
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection


def _relation_name_cell(s: str) -> str:
    t = normalize_text(s)
    if ":" in t:
        parts = t.split(":", 1)
        t = parts[-1].strip()
    return normalize_attribute_name(t)


def parse_task1(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    if not rows:
        return ParseOutcome.failure("Нет данных: пустая секция задания 1")
    rel_name = ""
    hi = 0
    # First row: single cell or "Название отношения" style
    first = rows[0]
    nones = [normalize_text(c or "") for c in first if c]
    if len(nones) == 1 and not any(sep in nones[0] for sep in [",", ";"]):
        rel_name = _relation_name_cell(nones[0])
        hi = 1
    # Find header row: first row with >=2 filled cells
    headers: list[str] = []
    start_data = 0
    found = False
    for i in range(hi, len(rows)):
        raw_nonempty = [c for c in rows[i] if c and str(c).strip()]
        if len(raw_nonempty) < 2:
            continue
        first_txt = normalize_text(str(raw_nonempty[0])).lower()
        second_txt = normalize_text(str(raw_nonempty[1])) if len(raw_nonempty) > 1 else ""
        # Строка-подсказка «Ответ:» + длинный текст — не заголовок таблицы.
        if first_txt.startswith("ответ:") and len(second_txt) > 30:
            continue
        cells = [normalize_attribute_name(c) for c in rows[i] if c and normalize_attribute_name(c)]
        if len(cells) >= 2:
            headers = cells
            start_data = i + 1
            found = True
            break
    if not found:
        return ParseOutcome.failure("Не найдена строка заголовков таблицы (нужно ≥2 атрибутов)")
    data_rows: list[tuple[str, ...]] = []
    for i in range(start_data, len(rows)):
        r = rows[i]
        vals: list[str] = []
        for j in range(max(len(r), len(headers))):
            v = r[j] if j < len(r) else None
            vals.append(normalize_cell_value(v))
        if all(not x for x in vals):
            continue
        # Pad/truncate to header length
        vals = vals[: len(headers)]
        while len(vals) < len(headers):
            vals.append("")
        data_rows.append(tuple(vals))
    out = {
        "relation": rel_name,
        "headers": headers,
        "rows": sorted(data_rows),  # multiset as sorted list for JSON
    }
    return ParseOutcome.success(out)
