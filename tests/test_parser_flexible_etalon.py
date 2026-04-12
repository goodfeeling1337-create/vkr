"""Регрессия: эталоны с «Ответ:», «нет», заголовками без «Отношение:»."""

from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.parsers import task_07, task_09, task_11_13


def test_task9_detects_net_after_answer_label() -> None:
    matrix = [
        ["Задание №9"],
        [None, "Ответ:", "нет"],
    ]
    parsed = build_parsed_workbook(matrix)
    r = task_09.parse_task9(parsed.sections[9])
    assert r.ok
    assert r.value["mode"] == "none"


def test_task7_ottsutstvuyut() -> None:
    matrix = [
        ["Задание №7"],
        [None, "Ответ:", "Отсутствуют"],
    ]
    parsed = build_parsed_workbook(matrix)
    r = task_07.parse_task7(parsed.sections[7])
    assert r.ok
    assert r.value["fd_lines"] == []


def test_task11_title_plus_header_row() -> None:
    matrix = [
        ["Задание №11"],
        [None, "Поставщик"],
        [None, "Код*", "Название", "Город*"],
        [None, "1", "ООО", "Москва"],
    ]
    parsed = build_parsed_workbook(matrix)
    r = task_11_13.parse_relations_schema(parsed.sections[11])
    assert r.ok
    rels = r.value["relations"]
    assert len(rels) >= 1
    names = {x["name"].lower() for x in rels}
    assert "поставщик" in names or any("поставщик" in n for n in names)
