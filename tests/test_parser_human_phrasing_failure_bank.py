"""Банк «человеческих» формулировок, на которых текущие парсеры не извлекают структуру."""

from __future__ import annotations

import pytest

from app.checker.common.parse_sections import build_parsed_workbook
from app.checker.parsers import task_04, task_05, task_06, task_07, task_08, task_09, task_11_13


@pytest.mark.parametrize(
    ("task_no", "text"),
    [
        (4, "Код услуги зависит от стоимости услуги"),
        (4, "Месяц функционально определяется через год"),
        (6, "Частичная зависимость описана словами без нотации"),
        (7, "Вложенные частичные зависимости проверены"),
        (7, "Существенных замечаний не выявлено"),
        (8, "Транзитивная зависимость описана словами"),
        (8, "Код услуги определяется через промежуточный атрибут"),
        (9, "Транзитивные не обнаружены"),
    ],
)
def test_human_phrase_without_arrow_fails_strict_fd_parsers(task_no: int, text: str) -> None:
    matrix = [[f"Задание №{task_no}"], [None, text]]
    parsed = build_parsed_workbook(matrix)
    section = parsed.sections[task_no]

    parser_map = {
        4: task_04.parse_task4,
        6: task_06.parse_task6,
        7: task_07.parse_task7,
        8: task_08.parse_task8,
        9: task_09.parse_task9,
    }
    result = parser_map[task_no](section)
    assert not result.ok


@pytest.mark.parametrize(
    "task_no",
    [11, 13],
)
def test_free_prose_without_schema_cannot_be_parsed(task_no: int) -> None:
    matrix = [
        [f"Задание №{task_no}"],
        [None, "Набор отношений приведен в описательном виде без табличной схемы"],
        [None, "Поля и ключи указаны в пояснительной записке"],
    ]
    parsed = build_parsed_workbook(matrix)
    result = task_11_13.parse_relations_schema(parsed.sections[task_no])
    assert not result.ok


def test_task5_prose_is_parsed_as_text_attribute_not_parse_error() -> None:
    """Текущее поведение task5: почти любой непустой текст даёт wrong, а не parse_error."""
    matrix = [
        ["Задание №5"],
        [None, "составной ключ берем как код кв. плюс месяц и год"],
    ]
    parsed = build_parsed_workbook(matrix)
    result = task_05.parse_task5(parsed.sections[5])
    assert result.ok
    assert result.value
    attrs = result.value.get("pk_attributes", [])
    assert attrs
