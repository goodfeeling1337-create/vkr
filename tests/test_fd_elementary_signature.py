"""Элементарное разложение ФЗ — устойчивость к разбиению строк."""

from app.checker.fd_algebra import elementary_fd_signature


def test_same_semantics_different_line_split() -> None:
    a = ["A -> B, C"]
    b = ["A -> B", "A -> C"]
    assert elementary_fd_signature(a) == elementary_fd_signature(b)


def test_order_irrelevant() -> None:
    x = ["A -> B", "B -> C"]
    y = ["B -> C", "A -> B"]
    assert elementary_fd_signature(x) == elementary_fd_signature(y)
