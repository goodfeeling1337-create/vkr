from __future__ import annotations

from typing import Iterator

from app.domain.error_models import TypicalError
from app.domain.semantic_models import ErrorCategory


def _catalog() -> list[TypicalError]:
    return [
        TypicalError(
            code="GROUP_NOT_REPEATED",
            title="Не выделена повторяющаяся группа",
            description="При декомпозиции исходного отношения не найдена или неверно выделена повторяющаяся группа атрибутов.",
            task_numbers=(2,),
            category=ErrorCategory.structural,
            recognition_criterion="Несовпадение наборов групп в задании 2 с эталоном.",
            example="Группы {A,B} и {C} перепутаны с {A},{B,C}.",
            student_explanation="Проверьте, что каждая группа соответствует повторяющемуся фрагменту схемы.",
            teacher_explanation="Сверяется структура групп с эталонной декомпозицией.",
        ),
        TypicalError(
            code="NF1_WRONG",
            title="Неверно построена 1НФ",
            description="Таблица не удовлетворяет требованиям первой нормальной формы (заголовки, строки, ключ).",
            task_numbers=(3,),
            category=ErrorCategory.structural,
            recognition_criterion="Расхождение заголовков, строк или ключа с эталоном; ключ не уникализирует строки.",
            example="Разные наборы строк при совпадающих заголовках.",
            student_explanation="Сравните заголовки, набор строк и атрибуты ключа с условием задания.",
            teacher_explanation="Проверка мультимножества строк и уникальности ключа по данным студента.",
        ),
        TypicalError(
            code="FD_CONFUSED",
            title="Перепутаны функциональные зависимости",
            description="Смысловые связи между атрибутами отражены неверно относительно эталона.",
            task_numbers=(4, 6, 7, 8, 9),
            category=ErrorCategory.logical,
            recognition_criterion="Неполное пересечение множеств элементарных ФЗ с эталоном.",
            example="A→B записано как составная зависимость от другого LHS.",
            student_explanation="Сопоставьте каждую ФЗ с эталоном: левая и правая части должны давать то же множество элементарных зависимостей.",
            teacher_explanation="Сравнение ведётся по каноническому множеству элементарных ФЗ.",
        ),
        TypicalError(
            code="FD_MISSING",
            title="Пропущены функциональные зависимости",
            description="Часть эталонных ФЗ отсутствует в ответе.",
            task_numbers=(4, 6, 7, 8, 9),
            category=ErrorCategory.logical,
            recognition_criterion="Recall по элементарным ФЗ < 1 при непустом эталоне.",
            example="Отсутствует элементарная ФЗ из разбиения эталонной строки.",
            student_explanation="Проверьте, что все зависимости из эталона выведены или перечислены.",
            teacher_explanation="По разности множеств эталон минус ответ.",
        ),
        TypicalError(
            code="FD_EXTRA",
            title="Лишние функциональные зависимости",
            description="В ответ включены зависимости, которых нет в эталоне.",
            task_numbers=(4, 6, 7, 8, 9),
            category=ErrorCategory.logical,
            recognition_criterion="Precision по элементарным ФЗ < 1.",
            example="Добавлена лишняя элементарная ФЗ, не выводимая из условия.",
            student_explanation="Уберите или обоснуйте зависимости, не следующие из условия.",
            teacher_explanation="Лишние элементарные ФЗ увеличивают ответ относительно эталона.",
        ),
        TypicalError(
            code="PK_WRONG",
            title="Неверно определён первичный ключ",
            description="Множество атрибутов ключа не совпадает с эталоном или не обеспечивает уникальность.",
            task_numbers=(5,),
            category=ErrorCategory.logical,
            recognition_criterion="Расхождение pk_attributes или нарушение уникальности по таблице из задания 3.",
            example="{A,B} вместо {A}.",
            student_explanation="Проверьте минимальность и уникальность ключа на строках 1НФ.",
            teacher_explanation="Сравнение множества атрибутов ключа и проверка уникальности.",
        ),
        TypicalError(
            code="PARTIAL_AS_FULL",
            title="Частичная зависимость принята за полную",
            description="На этапе частичных ФЗ смешаны уровни вложенности или игнорируется частичность.",
            task_numbers=(6,),
            category=ErrorCategory.methodical,
            recognition_criterion="Несовпадение множеств элементарных частичных ФЗ с эталоном.",
            example="Не выделены частичные зависимости от составного ключа.",
            student_explanation="Убедитесь, что учтены только частичные ФЗ относительно выбранного ключа.",
            teacher_explanation="Сравнение по elementary_fd_signature для частичных ФЗ.",
        ),
        TypicalError(
            code="TRANSITIVE_AS_PARTIAL",
            title="Транзитивная зависимость принята за частичную",
            description="На промежуточных шагах перепутаны типы зависимостей.",
            task_numbers=(7, 8),
            category=ErrorCategory.methodical,
            recognition_criterion="Несовпадение канонических множеств на шагах 7–8.",
            example="Цепочка A→B→C оформлена как частичная от ключа.",
            student_explanation="Различайте вложенные/частичные и транзитивные шаги по методике курса.",
            teacher_explanation="Семантика шага фиксируется парсером и сравнивается по элементарным ФЗ.",
        ),
        TypicalError(
            code="NESTED_FD_WRONG",
            title="Вложенные зависимости определены неверно",
            description="Структура вложенности по LHS не соответствует эталону.",
            task_numbers=(7, 9),
            category=ErrorCategory.logical,
            recognition_criterion="Несовпадение множеств элементарных ФЗ с особыми вложенными формами.",
            example="Краткая запись эквивалентна, но набор элементарных ФЗ отличается.",
            student_explanation="Проверьте вложенность и итоговые транзитивные цепочки.",
            teacher_explanation="Сравнение по элементарным сигнатурам с учётом режима задания 9.",
        ),
        TypicalError(
            code="SCHEMA_2NF_INCOMPLETE",
            title="Схема 2НФ неполная",
            description="Декомпозиция до 2НФ не совпадает с эталоном (связи, ключи, атрибуты).",
            task_numbers=(11,),
            category=ErrorCategory.structural,
            recognition_criterion="Канонические множества отношений не совпадают.",
            example="Отсутствует отношение или неверный ключ в одном из фрагментов.",
            student_explanation="Сверьте каждое отношение: имя, атрибуты, ключ — с эталоном.",
            teacher_explanation="Сравнение без учёта порядка отношений и атрибутов.",
        ),
        TypicalError(
            code="SCHEMA_3NF_INCOMPLETE",
            title="Схема 3НФ неполная",
            description="Декомпозиция до 3НФ не совпадает с эталоном.",
            task_numbers=(13,),
            category=ErrorCategory.structural,
            recognition_criterion="Канонические множества отношений не совпадают.",
            example="Лишнее или пропущенное отношение после устранения транзитивных зависимостей.",
            student_explanation="Проверьте итоговый набор отношений и ключей.",
            teacher_explanation="То же каноническое сравнение, что и для 2НФ, для финальной схемы.",
        ),
        TypicalError(
            code="JUNCTION_MISSING",
            title="Пропущено связующее отношение",
            description="В схеме отсутствует связующая сущность, ожидаемая эталоном (при строгом режиме).",
            task_numbers=(11, 13),
            category=ErrorCategory.structural,
            recognition_criterion="Несовпадение канонического набора; возможен режим permissive с опусканием чистых связей.",
            example="Отсутствует таблица связи M:N.",
            student_explanation="Проверьте наличие всех связей, в т.ч. связующих таблиц.",
            teacher_explanation="Зависит от флага allow_optional_pure_junction.",
        ),
        TypicalError(
            code="METHODICAL_MISMATCH",
            title="Структурно близко, но не по алгоритму",
            description="Ответ похож по составу, но не следует требуемой методике шага.",
            task_numbers=(4, 6, 7, 8, 9, 11, 13),
            category=ErrorCategory.methodical,
            recognition_criterion="Частичное пересечение с эталоном при формально разных шагах.",
            example="Иные цепочки вывода при близком множестве ФЗ.",
            student_explanation="Сверьтесь с порядком шагов в методичке.",
            teacher_explanation="Низкий recall/precision при семантическом сходстве.",
        ),
    ]


_CATALOG: dict[str, TypicalError] = {e.code: e for e in _catalog()}


class NormalizationErrorCatalog:
    """Каталог типовых ошибок, независимый от UI."""

    @staticmethod
    def all_errors() -> list[TypicalError]:
        return list(_CATALOG.values())

    @staticmethod
    def get(code: str) -> TypicalError | None:
        return _CATALOG.get(code)

    @staticmethod
    def for_task(task_number: int) -> Iterator[TypicalError]:
        for e in _CATALOG.values():
            if task_number in e.task_numbers:
                yield e


def list_codes() -> list[str]:
    return sorted(_CATALOG.keys())
