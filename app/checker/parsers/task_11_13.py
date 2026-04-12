from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_attribute_name, normalize_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

_REL_LINE = re.compile(
    r"^\s*(?:отношение|таблица|реляц(?:ия|ии)|схема)\s*[:\-]?\s*(?P<name>.+?)\s*$",
    re.IGNORECASE,
)

# «2. Отношение X», «(2НФ) Таблица …»
_REL_PREFIXED = re.compile(
    r"^\s*(?:\(\s*2\s*нф\s*\)|\(\s*3\s*нф\s*\)|\d+[\).]\s*)"
    r"(?:отношение|таблица|реляц(?:ия|ии)|схема)?\s*[:\-]?\s*(?P<name>.+?)\s*$",
    re.IGNORECASE,
)

# Строки-шум до таблиц отношений
_NOISE_PREFIX = re.compile(
    r"^\s*(ответ|2нф|3нф|2\s*нф|3\s*нф)\s*:?\s*$",
    re.IGNORECASE,
)


def _joined(row: list[str | None]) -> str:
    return " ".join(str(c) for c in row if c).strip()


def _is_noise_row(joined: str) -> bool:
    if not joined:
        return True
    if _NOISE_PREFIX.match(joined):
        return True
    low = joined.lower()
    if low.startswith("промежуточная") and len(joined) < 80:
        return True
    return False


def _grid_name_attrs_row(row: list[str | None]) -> dict[str, Any] | None:
    """
    Одна строка: имя отношения | атрибуты через запятую или в соседних ячейках.
    Частый формат в Excel без строки «Отношение:».
    """
    cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
    if len(cells) < 2:
        return None
    joined = " ".join(cells)
    if "->" in joined or "→" in joined:
        return None
    name = normalize_attribute_name(cells[0])
    if not name or len(name) > 200:
        return None
    low = name.lower()
    if low in {"имя", "отношение", "название", "атрибут", "ключ", "таблица", "схема", "реляция", "no", "№"}:
        return None
    attrs: set[str] = set()
    keys: set[str] = set()
    for piece in cells[1:]:
        for p in re.split(r"[,;]", piece):
            p = p.strip()
            if not p:
                continue
            is_key = "*" in p
            n = normalize_attribute_name(p.replace("*", ""))
            if n:
                attrs.add(n)
                if is_key:
                    keys.add(n)
    if not attrs:
        return None
    if re.match(r"^-?\d+$", name):
        return None
    return {"name": name, "attributes": sorted(attrs), "key_attributes": sorted(keys)}


def _single_title_cells(row: list[str | None]) -> str | None:
    """Одна смысловая ячейка — возможное имя отношения (без «Отношение:»)."""
    parts = [normalize_text(c) for c in row if c and normalize_text(c)]
    if len(parts) != 1:
        return None
    t = parts[0]
    if "->" in t or "→" in t:
        return None
    if len(t) > 200:
        return None
    if _REL_LINE.match(t):
        return None
    if _NOISE_PREFIX.match(t):
        return None
    low = t.lower()
    if low in {"2нф", "3нф", "2нф:", "3нф:"}:
        return None
    return t


def _looks_like_header_row(row: list[str | None]) -> bool:
    cells = [str(c).strip() for c in row if c and str(c).strip()]
    if len(cells) < 2:
        return False
    star = sum(1 for c in cells if "*" in c)
    return star >= 1 or len(cells) >= 3


def _attrs_keys_from_header(row: list[str | None]) -> tuple[set[str], set[str]]:
    attrs: set[str] = set()
    keys: set[str] = set()
    for c in row:
        if not c:
            continue
        s = str(c).strip()
        if not s:
            continue
        is_key = "*" in s
        name = normalize_attribute_name(s.replace("*", "").strip())
        if not name:
            continue
        attrs.add(name)
        if is_key:
            keys.add(name)
    return attrs, keys


def _is_data_row_not_header(row: list[str | None]) -> bool:
    """Эвристика: строка данных (много чисел/дат), не новый заголовок."""
    cells = [str(c).strip() for c in row if c and str(c).strip()]
    if len(cells) < 2:
        return False
    if _looks_like_header_row(row):
        return False
    num_like = 0
    for c in cells:
        if re.match(r"^-?\d+([.,]\d+)?$", c) or re.match(r"^\d{4}-\d{2}-\d{2}", c):
            num_like += 1
    return num_like >= len(cells) // 2 and len(cells) >= 2


def parse_relations_schema(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    """Парсинг схем: «Отношение X», либо заголовок-имя + строка атрибутов с *."""
    rows = non_empty_rows(section)
    rels: list[dict[str, Any]] = []
    i = 0
    while i < len(rows):
        row = rows[i]
        joined = _joined(row)
        if _is_noise_row(joined):
            i += 1
            continue

        m = _REL_LINE.match(joined) or _REL_PREFIXED.match(joined)
        if m:
            name = normalize_attribute_name(m.group("name"))
            attrs: set[str] = set()
            keys: set[str] = set()
            i += 1
            while i < len(rows):
                line = _joined(rows[i])
                if not line:
                    i += 1
                    continue
                if _REL_LINE.match(line) or _REL_PREFIXED.match(line):
                    break
                low = line.lower()
                if low.startswith("ключ") or low.startswith("pk") or "первичн" in low:
                    part = line.split(":", 1)[-1]
                    for p in re.split(r"[,;]", part):
                        if p.strip():
                            keys.add(normalize_attribute_name(p))
                elif low.startswith("атрибут"):
                    part = line.split(":", 1)[-1]
                    for p in re.split(r"[,;]", part):
                        if p.strip():
                            attrs.add(normalize_attribute_name(p))
                else:
                    for p in re.split(r"[,;]", line):
                        if p.strip():
                            attrs.add(normalize_attribute_name(p))
                i += 1
            rels.append({"name": name, "attributes": sorted(attrs), "key_attributes": sorted(keys)})
            continue

        title = _single_title_cells(row)
        if title and i + 1 < len(rows) and _looks_like_header_row(rows[i + 1]):
            attrs, keys = _attrs_keys_from_header(rows[i + 1])
            if attrs:
                rels.append(
                    {
                        "name": normalize_attribute_name(title),
                        "attributes": sorted(attrs),
                        "key_attributes": sorted(keys),
                    },
                )
                i += 2
                while i < len(rows):
                    jj = _joined(rows[i])
                    if not jj:
                        i += 1
                        continue
                    if _REL_LINE.match(jj) or _REL_PREFIXED.match(jj):
                        break
                    if _is_noise_row(jj):
                        i += 1
                        continue
                    if _single_title_cells(rows[i]) and i + 1 < len(rows) and _looks_like_header_row(rows[i + 1]):
                        break
                    if _looks_like_header_row(rows[i]) and not _is_data_row_not_header(rows[i]):
                        break
                    if _is_data_row_not_header(rows[i]):
                        i += 1
                        continue
                    i += 1
                continue

        gr = _grid_name_attrs_row(row)
        if gr and not _is_data_row_not_header(row):
            rels.append(gr)
            i += 1
            continue

        i += 1

    if not rels:
        for idx, row in enumerate(rows):
            joined = [normalize_attribute_name(str(c)) for c in row if c]
            if len(joined) >= 3 and joined[0].lower() in {"имя", "отношение", "название"}:
                for j in range(idx + 1, len(rows)):
                    r = rows[j]
                    if len(r) < 2:
                        continue
                    name = normalize_attribute_name(str(r[0] or ""))
                    rest = [normalize_attribute_name(str(x)) for x in r[1:] if x]
                    if not name:
                        continue
                    attrs = [x for x in rest if x]
                    rels.append({"name": name, "attributes": sorted(set(attrs)), "key_attributes": []})
                break

    if not rels:
        return ParseOutcome.failure("Не удалось распознать схемы отношений")
    return ParseOutcome.success({"relations": rels})
