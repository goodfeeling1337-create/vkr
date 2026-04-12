"""Заголовок секции с текстом формулировки в той же ячейке."""

from app.checker.common.section_locator import SectionLocator


def test_task_header_with_suffix_in_same_cell() -> None:
    matrix = [
        ["Задание №4 (про ФЗ). Дополнительный текст", ""],
    ]
    loc = SectionLocator(matrix)
    hits = loc.find_sections()
    assert 4 in hits
