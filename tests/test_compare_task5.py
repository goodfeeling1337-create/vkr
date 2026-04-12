from __future__ import annotations

from app.checker.checkers.compare import check_task5
from app.domain.check_results import TaskStatus


def test_pk_incomplete_subset() -> None:
    r = check_task5(
        {"pk_attributes": ["A", "B"]},
        {"pk_attributes": ["A"]},
        None,
        None,
    )
    assert r.status == TaskStatus.wrong
    assert any("Неполный первичный ключ" in e for e in r.errors)


def test_pk_redundant_superset() -> None:
    r = check_task5(
        {"pk_attributes": ["A"]},
        {"pk_attributes": ["A", "B"]},
        None,
        None,
    )
    assert r.status == TaskStatus.wrong
    assert any("Избыточный первичный ключ" in e for e in r.errors)


def test_pk_symmetric_mismatch() -> None:
    r = check_task5(
        {"pk_attributes": ["A", "B"]},
        {"pk_attributes": ["A", "C"]},
        None,
        None,
    )
    assert r.status == TaskStatus.wrong
    assert any("не совпадает с эталоном" in e for e in r.errors)


def test_pk_ok_with_unique_rows() -> None:
    t3 = {
        "headers": ["id", "name"],
        "rows": [("1", "a"), ("2", "b")],
    }
    r = check_task5(
        {"pk_attributes": ["id"]},
        {"pk_attributes": ["id"]},
        {"headers": ["id"]},
        t3,
    )
    assert r.status == TaskStatus.correct


def test_pk_duplicate_rows_flagged() -> None:
    t3 = {
        "headers": ["id", "name"],
        "rows": [("1", "a"), ("1", "b")],
    }
    r = check_task5(
        {"pk_attributes": ["id"]},
        {"pk_attributes": ["id"]},
        {"headers": ["id"]},
        t3,
    )
    assert r.status == TaskStatus.wrong
    assert any("дубликаты" in e for e in r.errors)
