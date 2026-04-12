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
                        matching_rule=te.matching_rule or None,
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
                            matching_rule=te.matching_rule or None,
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
                            matching_rule=te.matching_rule or None,
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
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add(code)
        if task_number in (11, 13) and stu_size > inter and precision < 1.0 and ref_size > 0:
            te = NormalizationErrorCatalog.get("SCHEMA_EXTRA_RELATIONS")
            if te and "SCHEMA_EXTRA_RELATIONS" not in matched_codes:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=min(0.6 + (1.0 - precision) * 0.35, 0.95),
                        student_message=te.student_explanation,
                        teacher_message=f"{te.teacher_explanation} (precision={precision:.2f})",
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add("SCHEMA_EXTRA_RELATIONS")

    if semantic and task_number in (11, 13):
        sgk = semantic.get("schema_gap_kind")
        if sgk == "extra_vs_ref" and "SCHEMA_EXTRA_RELATIONS" not in matched_codes:
            te = NormalizationErrorCatalog.get("SCHEMA_EXTRA_RELATIONS")
            if te:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.87,
                        student_message=te.student_explanation,
                        teacher_message=te.teacher_explanation,
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add("SCHEMA_EXTRA_RELATIONS")

    if semantic and task_number == 1:
        tg = semantic.get("table_gap_kind")
        cm = {
            "relation_name": "SOURCE_RELATION_NAME",
            "headers": "SOURCE_TABLE_HEADERS",
            "rows": "SOURCE_TABLE_ROWS",
        }
        c = cm.get(tg)
        if c and c not in matched_codes:
            te = NormalizationErrorCatalog.get(c)
            if te:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.9,
                        student_message=te.student_explanation,
                        teacher_message=te.teacher_explanation,
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add(c)

    if semantic and task_number == 2:
        gi = semantic.get("group_issue")
        cm = {"unknown_attr": "T2_UNKNOWN_ATTRIBUTE", "groups_mismatch": "GROUP_NOT_REPEATED"}
        c = cm.get(gi)
        if c and c not in matched_codes:
            te = NormalizationErrorCatalog.get(c)
            if te:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.88,
                        student_message=te.student_explanation,
                        teacher_message=te.teacher_explanation,
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add(c)

    if semantic and task_number == 3:
        nk = semantic.get("nf1_issue_kind")
        cm = {
            "relation_name": "NF1_RELATION_NAME",
            "headers": "NF1_HEADERS",
            "key_attributes": "NF1_KEY_ATTRS",
            "rows": "NF1_ROWS",
            "key_not_unique": "NF1_KEY_NOT_UNIQUE",
        }
        c = cm.get(nk)
        if c and c not in matched_codes:
            te = NormalizationErrorCatalog.get(c)
            if te:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.9,
                        student_message=te.student_explanation,
                        teacher_message=te.teacher_explanation,
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add(c)

    if semantic and task_number == 5:
        pk_kind = semantic.get("pk_kind")
        code_map = {
            "incomplete": "PK_INCOMPLETE",
            "redundant": "PK_REDUNDANT",
            "mismatch": "PK_WRONG",
            "not_unique_on_rows": "PK_NON_UNIQUE_ON_ROWS",
        }
        c = code_map.get(pk_kind)
        if c and c not in matched_codes:
            te = NormalizationErrorCatalog.get(c)
            if te:
                out.matches.append(
                    TypicalMistakeMatch(
                        code=te.code,
                        title=te.title,
                        category=te.category.value,
                        confidence=0.88,
                        student_message=te.student_explanation,
                        teacher_message=te.teacher_explanation,
                        matching_rule=te.matching_rule or None,
                    )
                )
                matched_codes.add(c)

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
