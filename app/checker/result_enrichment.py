from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.checker.error_analyzer import analyze_task_errors
from app.checker.grade_bands import semantic_mark_from_fd_sets, semantic_mark_from_status
from app.checker.semantic_compare import (
    compare_elementary_fd_sets,
    compare_relation_schemas,
    compare_task4_grouped_fd,
)
from app.domain.check_results import CheckReport, TaskCheckResult, TaskStatus
from app.domain.semantic_models import CHECK_RUN_VERSION, SemanticMark


FD_SEMANTIC_TASKS = frozenset({4, 6, 7, 8, 9})
SCHEMA_SEMANTIC_TASKS = frozenset({11, 13})


def enrich_task_result(
    task_number: int,
    tr: TaskCheckResult,
    *,
    ref_payload: dict[str, Any],
    stu_payload: dict[str, Any],
    allow_optional_pure_junction: bool,
) -> None:
    """Мутирует TaskCheckResult: semantic mark, typical mistakes, semantic_analysis."""
    if tr.status == TaskStatus.parse_error:
        tr.semantic_mark = None
        tr.semantic_mark_explanation = "Разбор ответа не выполнен — смысловая оценка недоступна."
        tr.typical_mistakes = []
        tr.semantic_analysis = {"status": "parse_error"}
        analysis = analyze_task_errors(task_number, tr, semantic=None)
        tr.typical_mistakes = [asdict(m) for m in analysis.matches] if analysis.matches else []
        return

    if task_number in FD_SEMANTIC_TASKS:
        # Задание 9: режим «нет цепочек» — нет строк ФЗ
        if task_number == 9:
            rm = ref_payload.get("mode", "chains")
            sm = stu_payload.get("mode", "chains")
            if rm == "none" and sm == "none":
                tr.semantic_analysis = {"mode": "none", "note": "Согласован отказ от транзитивных цепочек."}
                tr.semantic_mark = SemanticMark.pp.value
                tr.semantic_mark_explanation = "Оба ответа: нет транзитивных цепочек — полное согласие."
                analysis = analyze_task_errors(task_number, tr, semantic=tr.semantic_analysis)
                tr.typical_mistakes = [asdict(m) for m in analysis.matches]
                return
            if rm == "none" or sm == "none":
                tr.semantic_analysis = {"mode_mismatch": True, "ref_mode": rm, "stu_mode": sm}
                tr.semantic_mark = SemanticMark.mm.value
                tr.semantic_mark_explanation = "Несогласован режим ответа (наличие/отсутствие цепочек)."
                analysis = analyze_task_errors(task_number, tr, semantic=tr.semantic_analysis)
                tr.typical_mistakes = [asdict(m) for m in analysis.matches]
                return

        rlines = list(ref_payload.get("fd_lines") or [])
        slines = list(stu_payload.get("fd_lines") or [])
        cmp_el = compare_elementary_fd_sets(rlines, slines)
        sem = cmp_el.to_dict()
        if task_number == 4:
            gcmp = compare_task4_grouped_fd(rlines, slines)
            sem["task4_grouped"] = gcmp.to_dict()

        gb = semantic_mark_from_fd_sets(
            ref_elementary_count=cmp_el.ref_size,
            stu_elementary_count=cmp_el.stu_size,
            intersection=cmp_el.intersection,
        )
        mark = gb.mark
        expl = gb.explanation
        tr.semantic_analysis = sem
        tr.semantic_mark = mark.value
        tr.semantic_mark_explanation = expl

    elif task_number in SCHEMA_SEMANTIC_TASKS:
        cmp = compare_relation_schemas(
            ref_payload,
            stu_payload,
            allow_optional_pure_junction=allow_optional_pure_junction,
        )
        sem = cmp.to_dict()
        tr.semantic_analysis = sem
        gb = semantic_mark_from_fd_sets(
            ref_elementary_count=cmp.ref_size,
            stu_elementary_count=cmp.stu_size,
            intersection=cmp.intersection,
        )
        tr.semantic_mark = gb.mark.value
        tr.semantic_mark_explanation = gb.explanation

    else:
        is_ok = tr.status == TaskStatus.correct
        is_partial = tr.status == TaskStatus.partial
        gb = semantic_mark_from_status(is_correct=is_ok, is_partial=is_partial)
        tr.semantic_mark = gb.mark.value
        tr.semantic_mark_explanation = gb.explanation
        tr.semantic_analysis = {
            "status": tr.status.value,
            "note": "Отображение статуса на шкалу для не-ФЗ заданий.",
        }

    analysis = analyze_task_errors(task_number, tr, semantic=tr.semantic_analysis)
    tr.typical_mistakes = [asdict(m) for m in analysis.matches]


def finalize_report_semantics(report: CheckReport) -> None:
    """Сводка по блоку ФЗ и версия прогона."""
    fd_recalls: list[float] = []
    for n in sorted(FD_SEMANTIC_TASKS):
        tr = report.task_results.get(n)
        if not tr or tr.semantic_analysis is None:
            continue
        sa = tr.semantic_analysis
        if isinstance(sa, dict) and "recall" in sa:
            fd_recalls.append(float(sa["recall"]))

    mean_recall = sum(fd_recalls) / len(fd_recalls) if fd_recalls else None
    block_mark = None
    block_expl = None
    if fd_recalls:
        # Агрегат по блоку: та же шкала, что и по одному заданию, от среднего recall
        # Псевдо-счётчики для среднего recall: интерпретируем как «доля покрытия эталона в среднем»
        pseudo_ref = 100
        pseudo_inter = int(round(mean_recall * pseudo_ref)) if mean_recall is not None else 0
        gb = semantic_mark_from_fd_sets(
            ref_elementary_count=pseudo_ref,
            stu_elementary_count=pseudo_ref,
            intersection=min(pseudo_inter, pseudo_ref),
        )
        block_mark = gb.mark.value
        block_expl = (
            f"Сводка по заданиям {sorted(FD_SEMANTIC_TASKS)}: средняя доля покрытия эталонных "
            f"элементарных ФЗ ≈ {mean_recall:.2f}. Итоговая марка блока: {block_mark}."
        )

    report.check_run_version = CHECK_RUN_VERSION
    report.semantic_summary = {
        "fd_block_mean_recall": mean_recall,
        "fd_block_semantic_mark": block_mark,
        "fd_block_explanation": block_expl,
        "mark_summary": {
            "fd_block": block_mark,
            "mean_recall": mean_recall,
        },
        "per_task_fd_marks": {str(n): report.task_results[n].semantic_mark for n in FD_SEMANTIC_TASKS if n in report.task_results},
    }
    if report.metadata_resolution:
        report.semantic_summary["metadata_resolution_source"] = report.metadata_resolution
