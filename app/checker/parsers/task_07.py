from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_fd_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection


def parse_task7(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    """Extract FD lines with indentation level (2 spaces = 1 level)."""
    rows = non_empty_rows(section)
    entries: list[tuple[int, str]] = []
    for row in rows:
        for c in row:
            if not c:
                continue
            raw = str(c)
            for line in raw.splitlines():
                t = normalize_fd_text(line)
                if not t or "->" not in t:
                    continue
                lead = len(line) - len(line.lstrip(" \t"))
                level = 0
                m = re.match(r"^(\s*)", line)
                if m:
                    ws = m.group(1)
                    level = len(ws.replace("\t", "  "))
                entries.append((level, t))
    if not entries:
        return ParseOutcome.failure("Не найдены вложенные частичные ФЗ")
    lines_only = [e[1] for e in entries]
    return ParseOutcome.success({"fd_lines": lines_only, "levels": [e[0] for e in entries]})
