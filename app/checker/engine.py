from __future__ import annotations

import json
import logging
from typing import Any, Callable

from app.checker.checkers.compare import (
    check_task1,
    check_task11,
    check_task13,
    check_task2,
    check_task3,
    check_task4,
    check_task5,
    check_task6,
    check_task7,
    check_task8,
    check_task9,
)
from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.common.workbook_validator import WorkbookValidator
from app.checker.normalizers import normalize_attribute_name
from app.checker.reference_compiler import matrix_from_workbook
from app.checker.cross_task_checks import run_cross_task_checks  # NEW: cross-task checks
from app.checker.result_enrichment import enrich_task_result, finalize_report_semantics
from app.checker.scoring import AUTO_CHECKED_TASKS, MANUAL_ONLY_TASKS, max_score_for_task, total_max_score
from app.domain.check_results import CheckReport, TaskCheckResult, TaskStatus
from app.checker.parsers import (
    task_01,
    task_02,
    task_03,
    task_04,
    task_05,
    task_06,
    task_07,
    task_08,
    task_09,
    task_10_12,
    task_11_13,
)
from openpyxl.workbook.workbook import Workbook

log = logging.getLogger(__name__)


def _set_parse_error(
    report: CheckReport,
    n: int,
    max_s: float,
    human_msg_suffix: str,
    *,
    errors: list[str],
    reference_payloads: dict[int, Any],
    allow_optional_pure_junction: bool,
) -> None:
    """Set a parse_error TaskCheckResult and enrich it. Eliminates repeated boilerplate."""
    tr = TaskCheckResult(
        n,
        TaskStatus.parse_error,
        0.0,
        max_s,
        errors=errors,
        human_message=f"Не удалось распознать ответ по заданию {n}: {human_msg_suffix}",
    )
    report.task_results[n] = tr
    if n in AUTO_CHECKED_TASKS:
        enrich_task_result(
            n,
            tr,
            ref_payload=reference_payloads.get(n, {}),
            stu_payload={},
            allow_optional_pure_junction=allow_optional_pure_junction,
        )


def _attr_vocab(task1: dict[str, Any] | None) -> set[str]:
    if not task1:
        return set()
    h = [normalize_attribute_name(x) for x in task1.get("headers", [])]
    return set(h)


def run_check(
    wb: Workbook,
    reference_payloads: dict[int, dict[str, Any]],
    *,
    allow_optional_pure_junction: bool,
    metadata_resolution: str | None = None,
) -> CheckReport:
    v = WorkbookValidator().validate(wb, require_all_sections=False)
    report = CheckReport(
        metadata_resolution=metadata_resolution,
        workbook_structure_errors=list(v.errors),
        workbook_structure_warnings=list(v.warnings or []),
    )
    if not v.ok:
        for e in v.errors:
            log.warning("workbook validation: %s", e)
        # still try partial parse
    matrix = matrix_from_workbook(wb)
    try:
        parsed = build_parsed_workbook(matrix)
    except Exception as exc:  # noqa: BLE001
        log.exception("build_parsed_workbook failed: %s", exc)
        for t in AUTO_CHECKED_TASKS:
            report.task_results[t] = TaskCheckResult(
                t,
                TaskStatus.parse_error,
                0.0,
                max_score_for_task(t),
                errors=[str(exc)],
                human_message="Не удалось разобрать файл: внутренняя ошибка разбора секций",
            )
        for t in MANUAL_ONLY_TASKS:
            report.task_results[t] = TaskCheckResult(
                t,
                TaskStatus.not_checked,
                0.0,
                0.0,
                human_message="Проверяется преподавателем",
            )
        report.max_score = total_max_score()
        for t in AUTO_CHECKED_TASKS:
            enrich_task_result(
                t,
                report.task_results[t],
                ref_payload=reference_payloads.get(t, {}),
                stu_payload={},
                allow_optional_pure_junction=allow_optional_pure_junction,
            )
        finalize_report_semantics(report)
        return report

    ref1 = reference_payloads.get(1)

    parsers_map = {
        1: task_01.parse_task1,
        2: task_02.parse_task2,
        3: task_03.parse_task3,
        4: task_04.parse_task4,
        5: task_05.parse_task5,
        6: task_06.parse_task6,
        7: task_07.parse_task7,
        8: task_08.parse_task8,
        9: task_09.parse_task9,
        10: task_10_12.parse_raw_section,
        11: task_11_13.parse_relations_schema,
        12: task_10_12.parse_raw_section,
        13: task_11_13.parse_relations_schema,
    }

    vocab = _attr_vocab(ref1)
    ref3 = reference_payloads.get(3)
    stu3: dict[str, Any] | None = None

    for n in range(1, 14):
        max_s = max_score_for_task(n)
        if n not in parsed.sections:
            if n in MANUAL_ONLY_TASKS:
                report.task_results[n] = TaskCheckResult(
                    n,
                    TaskStatus.not_checked,
                    0.0,
                    0.0,
                    human_message="Проверяется преподавателем",
                )
                continue
            _set_parse_error(
                report, n, max_s, "секция отсутствует",
                errors=["Секция не найдена"],
                reference_payloads=reference_payloads,
                allow_optional_pure_junction=allow_optional_pure_junction,
            )
            continue
        fn = parsers_map[n]
        try:
            pr = fn(parsed.sections[n])
        except Exception as exc:  # noqa: BLE001
            log.exception("parser crash task %s: %s", n, exc)
            _set_parse_error(
                report, n, max_s, "ошибка разбора",
                errors=[f"Ошибка парсера: {exc}"],
                reference_payloads=reference_payloads,
                allow_optional_pure_junction=allow_optional_pure_junction,
            )
            continue
        if not pr.ok:
            _set_parse_error(
                report, n, max_s, pr.error or "ошибка разбора",
                errors=[pr.error or "parse error"],
                reference_payloads=reference_payloads,
                allow_optional_pure_junction=allow_optional_pure_junction,
            )
            continue
        payload = pr.value or {}
        if n == 3:
            stu3 = payload
        refp = reference_payloads.get(n, {})
        if n in MANUAL_ONLY_TASKS:
            report.task_results[n] = TaskCheckResult(
                n,
                TaskStatus.not_checked,
                0.0,
                0.0,
                parsed_answer=payload,
                expected_answer_snapshot=refp,
                human_message="Проверяется преподавателем",
            )
            continue
        if n not in AUTO_CHECKED_TASKS:
            continue
        checkers_map: dict[int, Callable[..., TaskCheckResult]] = {
            1: lambda ref, stu: check_task1(ref, stu),
            2: lambda ref, stu: check_task2(ref, stu, vocab),
            3: lambda ref, stu: check_task3(ref, stu),
            4: lambda ref, stu: check_task4(ref, stu, vocab),
            5: lambda ref, stu: check_task5(ref, stu, ref3, stu3),
            6: lambda ref, stu: check_task6(ref, stu),
            7: lambda ref, stu: check_task7(ref, stu),
            8: lambda ref, stu: check_task8(ref, stu),
            9: lambda ref, stu: check_task9(ref, stu),
            11: lambda ref, stu: check_task11(ref, stu, allow_optional_pure_junction),
            13: lambda ref, stu: check_task13(ref, stu, allow_optional_pure_junction),
        }
        try:
            checker = checkers_map.get(n)
            if checker is not None:
                tr = checker(refp, payload)
            else:
                tr = TaskCheckResult(n, TaskStatus.wrong, 0.0, max_s, errors=["unsupported"])
        except Exception as exc:  # noqa: BLE001
            log.exception("checker crash task %s: %s", n, exc)
            tr = TaskCheckResult(
                n,
                TaskStatus.parse_error,
                0.0,
                max_s,
                errors=[str(exc)],
                human_message=f"Ошибка проверки задания {n}",
            )
        report.task_results[n] = tr
        enrich_task_result(
            n,
            tr,
            ref_payload=refp,
            stu_payload=payload,
            allow_optional_pure_junction=allow_optional_pure_junction,
        )

    total = 0.0
    for _, tr in report.task_results.items():
        if tr.status == TaskStatus.correct:
            total += tr.score
        elif tr.status == TaskStatus.partial:
            total += tr.score
    report.total_score = total
    report.max_score = total_max_score()

    run_cross_task_checks(report)  # NEW: cross-task consistency checks
    finalize_report_semantics(report)
    return report


def report_to_json(report: CheckReport) -> str:
    return json.dumps(report.to_serializable(), ensure_ascii=False)
