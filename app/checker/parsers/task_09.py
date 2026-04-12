from __future__ import annotations

import re
from typing import Any

from app.checker.normalizers import normalize_fd_text
from app.checker.parsers.outcome import ParseOutcome
from app.checker.parsers.task_common import non_empty_rows
from app.domain.workbook import ParsedTaskSection

# «Нет транзитивных / цепочек» в свободной форме (после нормализации текста ответа)
_NO_CHAIN_RE = re.compile(
    r"(^|[\s,;])(нет|no|отсутствуют|отсутствует|не\s+существует)\b",
    re.IGNORECASE,
)


def _strip_answer_prefix(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^(ответ|задание)\s*[:.]?\s*", "", t, flags=re.IGNORECASE)
    return t.strip()


def parse_task9(section: ParsedTaskSection) -> ParseOutcome[dict[str, Any]]:
    rows = non_empty_rows(section)
    lines: list[str] = []
    for row in rows:
        for c in row:
            if not c:
                continue
            for line in str(c).splitlines():
                x = normalize_fd_text(line)
                if x and "->" in x:
                    lines.append(x)

    if lines:
        return ParseOutcome.success({"mode": "chains", "fd_lines": lines})

    # Без цепочек: ищем явный отказ («нет») в ячейках или в склейке текста
    cell_texts: list[str] = []
    for row in rows:
        for c in row:
            if c and str(c).strip():
                cell_texts.append(_strip_answer_prefix(str(c).strip()))

    for ct in cell_texts:
        low = ct.lower()
        if re.match(r"^(нет|no|отсутствуют|отсутствует)\s*[.!?…]?\s*$", low):
            return ParseOutcome.success({"mode": "none", "fd_lines": []})

    text = "\n".join(normalize_fd_text(str(c)) for row in rows for c in row if c and str(c).strip())
    text = _strip_answer_prefix(text)
    t = text.strip()
    if not t:
        return ParseOutcome.failure('Ожидалось "Нет" или цепочки с "->"')

    if re.match(r"^(нет|no|отсутствуют|отсутствует)\b", t, re.IGNORECASE):
        return ParseOutcome.success({"mode": "none", "fd_lines": []})
    if _NO_CHAIN_RE.search(t):
        return ParseOutcome.success({"mode": "none", "fd_lines": []})

    return ParseOutcome.failure('Ожидалось "Нет" или цепочки с "->"')
