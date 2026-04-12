from __future__ import annotations

import logging
from typing import Any

from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.common.workbook_validator import WorkbookValidator
from app.checker.reference_compiler import matrix_from_workbook
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

_PARSERS = {
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


def parse_all_tasks(wb: Workbook) -> dict[int, Any]:
    v = WorkbookValidator().validate(wb, require_all_sections=False)
    if not v.ok:
        log.warning("parse_all_tasks: workbook invalid: %s", v.errors)
    matrix = matrix_from_workbook(wb)
    parsed = build_parsed_workbook(matrix)
    out: dict[int, Any] = {}
    for n, fn in _PARSERS.items():
        sec = parsed.sections.get(n)
        if not sec:
            out[n] = {"parse_error": "section missing"}
            continue
        try:
            pr = fn(sec)
        except Exception as exc:  # noqa: BLE001
            out[n] = {"parse_error": str(exc)}
            continue
        if pr.ok:
            out[n] = pr.value
        else:
            out[n] = {"parse_error": pr.error}
    return out
