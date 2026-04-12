from __future__ import annotations

from typing import Any

from app.checker.error_catalog import NormalizationErrorCatalog
from app.checker.error_patterns import TEXT_PATTERNS
from app.domain.check_results import TaskCheckResult, TaskStatus
from app.domain.error_models import TaskErrorAnalysis, TypicalMistakeMatch


def analyze_task_errors(
    task_number: int,
    tr: TaskCheckResult,
    *,
    semantic: dict[str, Any] | None = None,
) -> TaskErrorAnalysis:
    """
    Сопоставление текста ошибок и семантических метрик с каталогом типовых ошибок.
    Не заменяет checker; даёт объяснимый слой для студента/преподавателя.
    """
    out = TaskErrorAnalysis(task_number=task_number)
    if tr.status == TaskStatus.parse_error:
        te = NormalizationErrorCatalog.get("NF1_WRONG")
        if te and task_number == 3:
            pass  # parse_error — отдельно, не навязываем NF1
        return out

    combined = " ".join(tr.errors or [])
    matched_codes: set[str] = set()

    for p in TEXT_PATTERNS:
        if p.task_numbers is not None and task_number not in p.task_numbers:
            continue
        if not p.keywords:
            continue
        if any(k.lower() in combined.lower() for k in p.keywords):
            te = NormalizationErrorCatalog.get(p.code)
            if te and task_number in te.task_numbers:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.65,
                        student_message=te.student_explanation,
                        teacher_message=te.teacher_explanation,
                    )
                )
                matched_codes.add(te.code)

    if semantic:
        recall = float(semantic.get("recall", 1.0))
        precision = float(semantic.get("precision", 1.0))
        ref_size = int(semantic.get("ref_size", 0))
        stu_size = int(semantic.get("stu_size", 0))
        inter = int(semantic.get("intersection", 0))

        if task_number in (4, 6, 7, 8, 9) and ref_size > 0:
            if recall < 1.0 and "FD_MISSING" not in matched_codes:
                te = NormalizationErrorCatalog.get("FD_MISSING")
                if te:
                    out.matches.append(
                        TypicalMistakeMatch(
                            code=te.code,
                            title=te.title,
                            category=te.category.value,
                            confidence=min(0.55 + (1.0 - recall) * 0.3, 0.95),
                            student_message=te.student_explanation,
                            teacher_message=f"{te.teacher_explanation} (recall={recall:.2f}, {inter}/{ref_size})",
                        )
                    )
                    matched_codes.add("FD_MISSING")
            if stu_size > inter and precision < 1.0 and "FD_EXTRA" not in matched_codes:
                te = NormalizationErrorCatalog.get("FD_EXTRA")
                if te:
                    out.matches.append(
                        TypicalMistakeMatch(
                            code=te.code,
                            title=te.title,
                            category=te.category.value,
                            confidence=min(0.55 + (1.0 - precision) * 0.3, 0.95),
                            student_message=te.student_explanation,
                            teacher_message=f"{te.teacher_explanation} (precision={precision:.2f})",
                        )
                    )

        if task_number in (11, 13) and ref_size > 0 and recall < 1.0:
            code = "SCHEMA_2NF_INCOMPLETE" if task_number == 11 else "SCHEMA_3NF_INCOMPLETE"
            te = NormalizationErrorCatalog.get(code)
            if te and code not in matched_codes:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.7,
                        student_message=te.student_explanation,
                        teacher_message=f"{te.teacher_explanation} (recall={recall:.2f})",
                    )
                )

    # Дедупликация по code, оставляем максимальную confidence
    by_code: dict[str, TypicalMistakeMatch] = {}
    for m in out.matches:
        prev = by_code.get(m.code)
        if prev is None or m.confidence > prev.confidence:
            by_code[m.code] = m
    out.matches = sorted(by_code.values(), key=lambda x: -x.confidence)

    if tr.status != TaskStatus.correct and not out.matches:
        out.raw_hints.append("Ответ отличается от эталона; уточните соответствие по условию задания.")

    return out
