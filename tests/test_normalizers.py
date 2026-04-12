from app.checker.normalizers import (
    normalize_arrow,
    normalize_attribute_name,
    normalize_fd_text,
    normalize_text,
)


def test_normalize_spaces() -> None:
    assert normalize_text("  a   b  ") == "a b"


def test_normalize_arrow() -> None:
    assert "->" in normalize_arrow("A → B")
    assert "->" in normalize_arrow("A=>B")


def test_normalize_fd_strip_filler() -> None:
    t = normalize_fd_text("Следовательно A -> B")
    assert "A" in t and "B" in t


def test_attribute_name() -> None:
    assert normalize_attribute_name("  `Name`  ") == "Name"
