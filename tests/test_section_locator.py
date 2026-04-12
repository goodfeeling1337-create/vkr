from app.checker.common.section_locator import SectionLocator


def test_prawilno_left_cell_still_finds_section() -> None:
    """Regression: 'Правильно' in another cell must not break 'Задание №5'."""
    matrix = [
        ["Правильно", "Задание №5", None],
        ["", "data", ""],
    ]
    loc = SectionLocator(matrix)
    hits = loc.find_sections()
    assert 5 in hits
    assert hits[5].row == 1


def test_per_cell_match() -> None:
    matrix = [
        ["", "", ""],
        ["Задание №1", "", ""],
    ]
    loc = SectionLocator(matrix)
    assert 1 in loc.find_sections()


def test_zadanie_without_nomer_sign() -> None:
    """«Задание 6» без символа № (логика из архивного locator)."""
    matrix = [["Задание 6", "текст условия"]]
    loc = SectionLocator(matrix)
    hits = loc.find_sections()
    assert 6 in hits
    assert hits[6].col == 1


def test_zadanie_space_after_nomer_sign() -> None:
    matrix = [["Задание № 6", "часть условия"]]
    loc = SectionLocator(matrix)
    assert 6 in loc.find_sections()
