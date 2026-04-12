from __future__ import annotations

from app.checker.normalizers import normalize_attribute_name, normalize_text
from app.domain.workbook import ParsedTaskSection


def non_empty_rows(section: ParsedTaskSection) -> list[list[str | None]]:
    return [r for r in section.rows if any(x and str(x).strip() for x in r)]


def row_strings(row: list[str | None]) -> list[str]:
    return [normalize_text(x or "") for x in row if x and normalize_text(x or "")]
