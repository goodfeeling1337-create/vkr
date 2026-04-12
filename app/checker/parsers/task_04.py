from __future__ import annotations

from typing import Any

from app.checker.normalizers import normalize_fd_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection


def parse_task4(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    lines: list[str] = []
    for row in rows:
        for c in row:
            if not c:
                continue
            for line in str(c).splitlines():
                t = normalize_fd_text(line)
                if t and "->" in t:
                    lines.append(t)
    if not lines:
        return ParseOutcome.failure("Не найдены строки функциональных зависимостей (ожидается 'A -> B')")
    return ParseOutcome.success({"fd_lines": lines})
