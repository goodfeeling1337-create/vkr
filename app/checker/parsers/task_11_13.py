from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_attribute_name
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

_REL_LINE = re.compile(
    r"^\s*отношение\s*[:\-]?\s*(?P<name>.+?)\s*$",
    re.IGNORECASE,
)


def parse_relations_schema(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    """Parse relation blocks: line 'Отношение X' then attrs line, optional key line."""
    rows = non_empty_rows(section)
    rels: list[dict[str, Any]] = []
    i = 0
    while i < len(rows):
        row = rows[i]
        joined = " ".join(str(c) for c in row if c).strip()
        m = _REL_LINE.match(joined)
        if m:
            name = normalize_attribute_name(m.group("name"))
            attrs: set[str] = set()
            keys: set[str] = set()
            i += 1
            while i < len(rows):
                line = " ".join(str(c) for c in rows[i] if c).strip()
                if not line:
                    i += 1
                    continue
                if _REL_LINE.match(line):
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
        i += 1
    if not rels:
        # table shape: header row Name | Attributes | Key
        for idx, row in enumerate(rows):
            joined = [normalize_attribute_name(str(c)) for c in row if c]
            if len(joined) >= 3 and joined[0].lower() in {"имя", "отношение", "название"}:
                # data follows
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
