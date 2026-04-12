from __future__ import annotations

from app.domain.error_models import ErrorPattern

# Эвристики: ключевые фразы из сообщений checker → код каталога
TEXT_PATTERNS: list[ErrorPattern] = [
    ErrorPattern("NF1_WRONG", (3,), ("Заголовки", "Строки", "ключ", "уникализирует")),
    ErrorPattern("PK_WRONG", (5,), ("ключ", "первичн", "атрибутов первичного")),
    ErrorPattern("FD_CONFUSED", (4, 6, 7, 8, 9), ("ФЗ", "функциональн", "элементарн", "не совпадает")),
    ErrorPattern("SCHEMA_2NF_INCOMPLETE", (11,), ("2НФ", "отношений")),
    ErrorPattern("SCHEMA_3NF_INCOMPLETE", (13,), ("3НФ", "отношений")),
    ErrorPattern("GROUP_NOT_REPEATED", (2,), ("групп", "атрибут")),
]

RECALL_PATTERNS: list[ErrorPattern] = [
    ErrorPattern("FD_MISSING", None, min_recall=0.0, max_recall=0.99),
    ErrorPattern("FD_EXTRA", None, min_recall=0.0, max_recall=1.0),
]
