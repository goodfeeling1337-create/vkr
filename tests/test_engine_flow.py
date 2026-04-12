from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.parsers import task_03


def test_task3_parse_error_incomplete_table() -> None:
    matrix = [
        ["Задание №3"],
        ["only_one_cell"],
    ]
    parsed = build_parsed_workbook(matrix)
    sec = parsed.sections[3]
    r = task_03.parse_task3(sec)
    assert not r.ok
    assert r.error
