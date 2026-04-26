from __future__ import annotations

from app.checker.checkers.compare import check_task1, check_task11, check_task3
from app.domain.check_results import TaskStatus


def test_task1_relation_error_message() -> None:
    ref = {"relation": "R", "headers": ["a"], "rows": [("1",)]}
    stu = {"relation": "S", "headers": ["a"], "rows": [("1",)]}
    r = check_task1(ref, stu)
    assert r.status == TaskStatus.wrong
    assert any("исходного отношения" in e for e in r.errors)


def test_task1_rows_equal_when_ref_lists_and_student_tuples() -> None:
    ref = {"relation": "R", "headers": ["a", "b"], "rows": [["1", "2"], ["3", "4"]]}
    stu = {"relation": "R", "headers": ["a", "b"], "rows": [("1", "2"), ("3", "4")]}
    r = check_task1(ref, stu)
    assert r.status == TaskStatus.correct


def test_task3_headers_nf1_message() -> None:
    ref = {
        "relation": "T",
        "headers": ["a", "b"],
        "key_attributes": ["a"],
        "rows": [("1", "2")],
    }
    stu = {
        "relation": "T",
        "headers": ["a", "c"],
        "key_attributes": ["a"],
        "rows": [("1", "2")],
    }
    r = check_task3(ref, stu)
    assert r.status == TaskStatus.wrong
    assert any("Заголовки столбцов 1НФ" in e for e in r.errors)


def test_task3_trailing_empty_headers_do_not_break_match() -> None:
    ref = {
        "relation": "T",
        "headers": ["", "a", "b", "", ""],
        "key_attributes": ["a"],
        "rows": [["", "1", "2", "", ""], ["", "3", "4", "", ""]],
    }
    stu = {
        "relation": "T",
        "headers": ["", "a", "b"],
        "key_attributes": ["a"],
        "rows": [("", "1", "2"), ("", "3", "4")],
    }
    r = check_task3(ref, stu)
    assert r.status == TaskStatus.correct


def test_task11_lists_missing_relation() -> None:
    ref = {
        "relations": [
            {"name": "A", "attributes": ["x"], "key_attributes": ["x"]},
            {"name": "B", "attributes": ["y", "z"], "key_attributes": ["y"]},
        ],
    }
    stu = {"relations": [{"name": "A", "attributes": ["x"], "key_attributes": ["x"]}]}
    r = check_task11(ref, stu, allow_optional_pure_junction=False)
    assert r.status == TaskStatus.wrong
    assert any("Нет в ответе" in e or "2НФ" in e for e in r.errors)
    assert any("B(" in e for e in r.errors)
