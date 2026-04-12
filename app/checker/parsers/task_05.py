from __future__ import annotations

from typing import Any

from app.checker.normalizers import normalize_attribute_name
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection


def parse_task5(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    attrs: set[str] = set()
    for row in rows:
        non = [str(c).strip() for c in row if c and str(c).strip()]
        if not non:
            continue
        if len(non) == 1:
            attrs.add(normalize_attribute_name(non[0]))
        else:
            # single row with many attrs
            line = " ".join(non)
            for part in line.replace(";", ",").split(","):
                if part.strip():
                    attrs.add(normalize_attribute_name(part))
    if not attrs:
        return ParseOutcome.failure("Не найдены атрибуты первичного ключа")
    return ParseOutcome.success({"pk_attributes": sorted(attrs)})
