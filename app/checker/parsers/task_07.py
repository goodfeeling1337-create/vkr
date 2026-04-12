from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_fd_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

# Нет вложенных частичных ФЗ (текстовый ответ без стрелок)
_NO_PARTIAL_RE = re.compile(
    r"(^|[\s,;])(нет|отсутствуют|отсутствует|отсутствуют\s+вложенные|no)\b",
    re.IGNORECASE,
)


def parse_task7(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    """Частичные ФЗ со стрелками; либо явное «нет/отсутствуют» без зависимостей."""
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
                m = re.match(r"^(\s*)", line)
                ws = m.group(1) if m else ""
                level = len(ws.replace("\t", "  "))
                entries.append((level, t))

    if entries:
        lines_only = [e[1] for e in entries]
        return ParseOutcome.success({"fd_lines": lines_only, "levels": [e[0] for e in entries]})

    blob = " ".join(
        normalize_fd_text(str(c))
        for row in rows
        for c in row
        if c and str(c).strip()
    )
    blob = re.sub(r"^(ответ|задание)\s*[:.]?\s*", "", blob, flags=re.IGNORECASE).strip()

    if _NO_PARTIAL_RE.search(blob):
        return ParseOutcome.success({"fd_lines": [], "levels": []})

    # Одна ячейка «нет»
    for row in rows:
        for c in row:
            if not c:
                continue
            s = str(c).strip().lower()
            if re.match(r"^(нет|отсутствуют|отсутствует|no)\s*[.!?…]?\s*$", s):
                return ParseOutcome.success({"fd_lines": [], "levels": []})

    return ParseOutcome.failure("Не найдены вложенные частичные ФЗ")
