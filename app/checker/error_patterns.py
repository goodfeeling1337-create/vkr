from __future__ import annotations

from app.domain.error_models import ErrorPattern

# Эвристики: ключевые фразы из сообщений checker → код каталога
TEXT_PATTERNS: list[ErrorPattern] = [
    ErrorPattern("SOURCE_RELATION_NAME", (1,), ("Название исходного отношения не совпадает",)),
    ErrorPattern("SOURCE_TABLE_HEADERS", (1,), ("Заголовки атрибутов не совпадают",)),
    ErrorPattern("SOURCE_TABLE_ROWS", (1,), ("Набор строк не совпадает с эталоном",)),
    ErrorPattern("T2_UNKNOWN_ATTRIBUTE", (2,), ("Неизвестный атрибут в группе",)),
    ErrorPattern("GROUP_NOT_REPEATED", (2,), ("Набор групп повторяющихся атрибутов не совпадает",)),
    ErrorPattern("NF1_RELATION_NAME", (3,), ("Название отношения в задании 3",)),
    ErrorPattern("NF1_HEADERS", (3,), ("Заголовки столбцов 1НФ",)),
    ErrorPattern("NF1_KEY_ATTRS", (3,), ("Ключевые атрибуты 1НФ",)),
    ErrorPattern("NF1_ROWS", (3,), ("Строки данных 1НФ",)),
    ErrorPattern("NF1_KEY_NOT_UNIQUE", (3,), ("не уникализирует строки", "дубликаты по ключу")),
    ErrorPattern("FD_ATTR_NOT_IN_VOCAB", (4,), ("не из словаря задания 1",)),
    ErrorPattern("PK_INCOMPLETE", (5,), ("Неполный первичный ключ",)),
    ErrorPattern("PK_REDUNDANT", (5,), ("Избыточный первичный ключ",)),
    ErrorPattern("PK_NON_UNIQUE_ON_ROWS", (5,), ("не уникализирует", "дубликаты")),
    ErrorPattern("PK_WRONG", (5,), ("Множество атрибутов первичного ключа не совпадает с эталоном",)),
    ErrorPattern(
        "FD_CONFUSED",
        (4, 6, 7, 8, 9),
        ("ФЗ", "функциональн", "элементарн", "не совпадает", "канонизац", "транзитив"),
    ),
    ErrorPattern("SCHEMA_2NF_INCOMPLETE", (11,), ("2НФ", "Нет в ответе", "отличается от эталона")),
    ErrorPattern("SCHEMA_3NF_INCOMPLETE", (13,), ("3НФ", "Нет в ответе", "отличается от эталона")),
    ErrorPattern("SCHEMA_EXTRA_RELATIONS", (11, 13), ("Лишние отношения",)),
]

RECALL_PATTERNS: list[ErrorPattern] = [
    ErrorPattern("FD_MISSING", None, min_recall=0.0, max_recall=0.99),
    ErrorPattern("FD_EXTRA", None, min_recall=0.0, max_recall=1.0),
]
