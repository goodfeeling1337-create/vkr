"""Ограничение отчёта для студента в режиме тестирования (без раскрытия эталона)."""

from __future__ import annotations

import copy
from typing import Any


def student_testing_report_view(report: dict[str, Any]) -> dict[str, Any]:
    """Убирает подсказки, семантику и текст ошибок; оставляет статусы и баллы."""
    r = copy.deepcopy(report)
    r.pop("semantic_summary", None)
    r.pop("metadata_resolution", None)
    r.pop("workbook_structure_warnings", None)
    r["workbook_structure_errors"] = list(r.get("workbook_structure_errors") or [])
    if r["workbook_structure_errors"]:
        r["workbook_structure_errors"] = ["Структура файла: см. общий статус (детали скрыты в режиме тестирования)."]
    tasks = r.get("tasks") or {}
    for _k, t in list(tasks.items()):
        if not isinstance(t, dict):
            continue
        t.pop("typical_mistakes", None)
        t.pop("semantic_mark_explanation", None)
        t.pop("semantic_analysis", None)
        if t.get("semantic_mark"):
            t["semantic_mark"] = "—"
        if t.get("errors"):
            t["errors"] = ["Детали скрыты в режиме тестирования."]
        if t.get("human_message"):
            t["human_message"] = None
    r["check_run_version"] = r.get("check_run_version")
    return r
