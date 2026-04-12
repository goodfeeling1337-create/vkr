from __future__ import annotations

import json
from typing import Any

from openpyxl.workbook.workbook import Workbook

from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.common.workbook_validator import WorkbookValidator, data_sheet_names
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


def matrix_from_workbook(wb: Workbook) -> list[list[Any]]:
    names = data_sheet_names(wb)
    if not names:
        raise ValueError("Нет листа с заданиями")
    ws = wb[names[0]]
    matrix: list[list[Any]] = []
    for row in ws.iter_rows(values_only=True):
        matrix.append(list(row))
    return matrix


def compile_reference_payloads(wb: Workbook) -> tuple[dict[int, dict[str, Any]], list[str]]:
    v = WorkbookValidator().validate(wb)
    if not v.ok:
        return {}, v.errors
    matrix = matrix_from_workbook(wb)
    parsed = build_parsed_workbook(matrix)
    out: dict[int, dict[str, Any]] = {}
    parsers = {
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
    errors: list[str] = []
    for n, fn in parsers.items():
        sec = parsed.sections.get(n)
        if not sec:
            errors.append(f"Отсутствует секция задания {n}")
            continue
        r = fn(sec)
        if not r.ok:
            errors.append(f"Эталон: не удалось разобрать задание {n}: {r.error}")
            continue
        out[n] = r.value or {}
    return out, errors


def payloads_to_db_rows(payloads: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {k: v for k, v in payloads.items()}


def snapshot_json(payloads: dict[int, dict[str, Any]]) -> str:
    return json.dumps({str(k): v for k, v in sorted(payloads.items())}, ensure_ascii=False)
