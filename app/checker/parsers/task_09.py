from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_fd_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection


def parse_task9(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    text = "\n".join(
        normalize_fd_text(str(c))
        for row in rows
        for c in row
        if c and str(c).strip()
    )
    t = text.strip()
    if re.match(r"^(нет|no)\b", t, re.IGNORECASE):
        return ParseOutcome.success({"mode": "none", "fd_lines": []})
    lines: list[str] = []
    for row in rows:
        for c in row:
            if not c:
                continue
            for line in str(c).splitlines():
                x = normalize_fd_text(line)
                if x and "->" in x:
                    lines.append(x)
    if not lines:
        return ParseOutcome.failure('Ожидалось "Нет" или цепочки с "->"')
    return ParseOutcome.success({"mode": "chains", "fd_lines": lines})
