"""Задание 3: формат без отдельной строки названия отношения."""

from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.parsers import task_03


def test_headers_first_row_without_relation_name() -> None:
    matrix = [
        ["Задание №3"],
        ["A*", "B"],
        ["1", "2"],
    ]
    parsed = build_parsed_workbook(matrix)
    sec = parsed.sections[3]
    r = task_03.parse_task3(sec)
    assert r.ok
    assert r.value
    assert r.value.get("relation") == ""
    assert "A" in r.value.get("headers", [])
