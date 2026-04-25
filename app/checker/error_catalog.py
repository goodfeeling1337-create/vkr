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
            code="T2_UNKNOWN_ATTRIBUTE",
            title="Атрибут вне словаря задания 1",
            description="В группе указан атрибут, которого нет среди заголовков исходного отношения.",
            task_numbers=(2,),
            category=ErrorCategory.structural,
            recognition_criterion="Сообщение проверки о неизвестном атрибуте в группе.",
            example="В группе указан X, которого нет в задании 1.",
            student_explanation="Используйте только имена атрибутов из таблицы задания 1.",
            teacher_explanation="Сверка групп с множеством имён из эталона задания 1.",
            matching_rule="Каждый атрибут ∈ словаря задания 1.",
        ),
        TypicalError(
            code="SOURCE_RELATION_NAME",
            title="Неверное имя исходного отношения",
            description="Название отношения в задании 1 не совпадает с эталоном.",
            task_numbers=(1,),
            category=ErrorCategory.structural,
            recognition_criterion="Расхождение поля relation с эталоном.",
            example="R вместо R1.",
            student_explanation="Сверьте строку с названием отношения с условием и эталоном.",
            teacher_explanation="Строковое сравнение нормализованных имён.",
        ),
        TypicalError(
            code="SOURCE_TABLE_HEADERS",
            title="Заголовки исходной таблицы не совпадают",
            description="Набор имён столбцов в задании 1 отличается от эталона.",
            task_numbers=(1,),
            category=ErrorCategory.structural,
            recognition_criterion="Покомпонентное сравнение списка заголовков.",
            example="Пропущен или лишний столбец.",
            student_explanation="Проверьте порядок и состав заголовков как в эталоне.",
            teacher_explanation="Сравнение списков заголовков после нормализации имён.",
        ),
        TypicalError(
            code="SOURCE_TABLE_ROWS",
            title="Строки исходной таблицы не совпадают",
            description="Мультимножество строк в задании 1 отличается от эталона.",
            task_numbers=(1,),
            category=ErrorCategory.structural,
            recognition_criterion="Сравнение отсортированных кортежей строк.",
            example="Другая строка или дубликат.",
            student_explanation="Сверьте каждую строку данных с эталоном (включая повторы).",
            teacher_explanation="Сравнение мультимножества строк.",
        ),
        TypicalError(
            code="NF1_RELATION_NAME",
            title="Неверное имя отношения в 1НФ",
            description="Название отношения в задании 3 не совпадает с эталоном (если оно задано в эталоне).",
            task_numbers=(3,),
            category=ErrorCategory.structural,
            recognition_criterion="Несовпадение relation при непустом эталоне.",
            example="Другое имя таблицы.",
            student_explanation="Сверьте имя отношения с эталоном.",
            teacher_explanation="Сравнение нормализованных строк названия.",
        ),
        TypicalError(
            code="NF1_HEADERS",
            title="Заголовки 1НФ не совпадают",
            description="Состав или порядок столбцов таблицы 1НФ отличается от эталона.",
            task_numbers=(3,),
            category=ErrorCategory.structural,
            recognition_criterion="Покомпонентное сравнение заголовков.",
            example="Переставлены столбцы или другой набор имён.",
            student_explanation="Заголовки должны в точности соответствовать эталону.",
            teacher_explanation="Построчное сравнение списка заголовков.",
        ),
        TypicalError(
            code="NF1_KEY_ATTRS",
            title="Ключевые атрибуты 1НФ не совпадают",
            description="Множество атрибутов ключа в таблице 1НФ отличается от эталона.",
            task_numbers=(3,),
            category=ErrorCategory.structural,
            recognition_criterion="Сравнение множеств key_attributes.",
            example="В ключ включён лишний атрибут.",
            student_explanation="Сверьте выделение ключевых атрибутов с эталоном.",
            teacher_explanation="Сравнение отсортированных списков ключевых имён.",
        ),
        TypicalError(
            code="NF1_ROWS",
            title="Строки данных 1НФ не совпадают",
            description="Мультимножество строк таблицы отличается от эталона.",
            task_numbers=(3,),
            category=ErrorCategory.structural,
            recognition_criterion="Сравнение мультимножества кортежей строк.",
            example="Иная строка или неверное число повторов.",
            student_explanation="Сверьте все строки с эталоном построчно.",
            teacher_explanation="Сравнение отсортированных списков строк.",
        ),
        TypicalError(
            code="NF1_KEY_NOT_UNIQUE",
            title="Ключ не уникализирует строки 1НФ",
            description="По указанным ключевым столбцам есть повторяющиеся строки.",
            task_numbers=(3,),
            category=ErrorCategory.semantic,
            recognition_criterion="Проекция строк на индексы ключевых атрибутов содержит дубликаты.",
            example="Две строки с одинаковым ключом.",
            student_explanation="В 1НФ ключ должен однозначно определять строку.",
            teacher_explanation="Проверка уникальности по индексам key_attributes.",
            matching_rule="Все значения ключа на строках уникальны.",
        ),
        TypicalError(
            code="FD_ATTR_NOT_IN_VOCAB",
            title="Атрибут ФЗ вне словаря задания 1",
            description="В ФЗ задания 4 используется имя атрибута, которого нет в эталоне задания 1.",
            task_numbers=(4,),
            category=ErrorCategory.structural,
            recognition_criterion="Атрибут в левой или правой части ФЗ ∉ словаря.",
            example="Опечатка в имени атрибута.",
            student_explanation="Используйте только атрибуты из таблицы задания 1.",
            teacher_explanation="Проверка вхождения имён в словарь эталона задания 1.",
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
            category=ErrorCategory.semantic,
            recognition_criterion="Неполное пересечение множеств элементарных ФЗ с эталоном.",
            example="A→B записано как составная зависимость от другого LHS.",
            student_explanation="Сопоставьте каждую ФЗ с эталоном: левая и правая части должны давать то же множество элементарных зависимостей.",
            teacher_explanation="Сравнение ведётся по каноническому множеству элементарных ФЗ.",
            matching_rule="Сравнение множеств элементарных ФЗ (каноническая форма).",
        ),
        TypicalError(
            code="FD_MISSING",
            title="Пропущены функциональные зависимости",
            description="Часть эталонных ФЗ отсутствует в ответе.",
            task_numbers=(4, 6, 7, 8, 9),
            category=ErrorCategory.semantic,
            recognition_criterion="Recall по элементарным ФЗ < 1 при непустом эталоне.",
            example="Отсутствует элементарная ФЗ из разбиения эталонной строки.",
            student_explanation="Проверьте, что все зависимости из эталона выведены или перечислены.",
            teacher_explanation="По разности множеств эталон минус ответ.",
            matching_rule="Recall = |F эталон ∩ F студент| / |F эталон|.",
        ),
        TypicalError(
            code="FD_EXTRA",
            title="Лишние функциональные зависимости",
            description="В ответ включены зависимости, которых нет в эталоне.",
            task_numbers=(4, 6, 7, 8, 9),
            category=ErrorCategory.semantic,
            recognition_criterion="Precision по элементарным ФЗ < 1.",
            example="Добавлена лишняя элементарная ФЗ, не выводимая из условия.",
            student_explanation="Уберите или обоснуйте зависимости, не следующие из условия.",
            teacher_explanation="Лишние элементарные ФЗ увеличивают ответ относительно эталона.",
            matching_rule="Precision = |пересечение| / |F студент|.",
        ),
        TypicalError(
            code="PK_INCOMPLETE",
            title="Неполный первичный ключ",
            description="В ключ включены не все атрибуты, необходимые по эталону.",
            task_numbers=(5,),
            category=ErrorCategory.semantic,
            recognition_criterion="Множество атрибутов ключа студента — строгое подмножество эталонного.",
            example="Эталон {A,B}, ответ {A}.",
            student_explanation="Сравните состав ключа с эталоном: не пропустите ли атрибут, входящий в минимальный ключ.",
            teacher_explanation="Проверка: stu_pk ⊂ ref_pk (оба как множества имён атрибутов).",
            matching_rule="stu_pk ⊂ ref_pk, stu_pk ≠ ref_pk.",
        ),
        TypicalError(
            code="PK_REDUNDANT",
            title="Избыточный первичный ключ",
            description="В ключ включены лишние атрибуты относительно эталона.",
            task_numbers=(5,),
            category=ErrorCategory.semantic,
            recognition_criterion="Множество атрибутов ключа студента строго шире эталонного.",
            example="Эталон {A}, ответ {A,B}.",
            student_explanation="Убедитесь, что ключ минимален: лишние атрибуты делают ключ не совпадающим с эталоном.",
            teacher_explanation="Проверка: ref_pk ⊂ stu_pk, stu_pk ≠ ref_pk.",
            matching_rule="ref_pk ⊂ stu_pk, stu_pk ≠ ref_pk.",
        ),
        TypicalError(
            code="PK_WRONG",
            title="Несовпадение состава первичного ключа",
            description="Набор атрибутов ключа отличается от эталона без отношения «подмножество».",
            task_numbers=(5,),
            category=ErrorCategory.semantic,
            recognition_criterion="Множества атрибутов ключа не равны и ни одно не является подмножеством другого.",
            example="{A,C} вместо {A,B}.",
            student_explanation="Сверьте каждый атрибут ключа с эталоном; возможна путаница имён или лишний/пропущенный атрибут.",
            teacher_explanation="Симметрическая разность множеств без включения.",
            matching_rule="stu_pk ≠ ref_pk и не (stu_pk ⊂ ref_pk) и не (ref_pk ⊂ stu_pk).",
        ),
        TypicalError(
            code="PK_NON_UNIQUE_ON_ROWS",
            title="Ключ не уникализирует строки таблицы 1НФ",
            description="По данным задания 3 выбранный ключ не различает дублирующиеся строки.",
            task_numbers=(5,),
            category=ErrorCategory.semantic,
            recognition_criterion="Дубликаты строк по проекции на атрибуты ключа в таблице студента.",
            example="Две строки с одинаковыми значениями по полям ключа.",
            student_explanation="Проверьте уникальность: на строках 1НФ не должно быть повторов по выбранному ключу.",
            teacher_explanation="Проверка _key_unique по строкам задания 3.",
            matching_rule="∃ две строки с одинаковыми значениями на атрибутах stu_pk.",
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
            category=ErrorCategory.semantic,
            recognition_criterion="Несовпадение множеств элементарных ФЗ с особыми вложенными формами.",
            example="Краткая запись эквивалентна, но набор элементарных ФЗ отличается.",
            student_explanation="Проверьте вложенность и итоговые транзитивные цепочки.",
            teacher_explanation="Сравнение по элементарным сигнатурам с учётом режима задания 9.",
            matching_rule="Элементарные ФЗ после развёртки вложенных форм.",
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
            code="SCHEMA_EXTRA_RELATIONS",
            title="Лишние отношения в схеме",
            description="В ответе есть канонические отношения, которых нет в эталоне (при том что эталон полностью не покрыт или покрыт частично).",
            task_numbers=(11, 13),
            category=ErrorCategory.semantic,
            recognition_criterion="Precision по множеству канонических отношений < 1 при непустом ответе.",
            example="Добавлена лишняя таблица или дублирующее отношение.",
            student_explanation="Уберите отношения, не следующие из условия и эталонной декомпозиции.",
            teacher_explanation="Сравнение канонических множеств отношений; лишние фрагменты снижают precision.",
            matching_rule="|R эталон ∩ R студент| / |R студент| < 1.",
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
        # NEW: EXAMPLE_VIOLATES_FD
        TypicalError(
            code="EXAMPLE_VIOLATES_FD",
            title="Контрольный пример нарушает ФЗ",
            description="Данные таблицы задания 1 нарушают функциональные зависимости, указанные в задании 4.",
            task_numbers=(1,),
            category=ErrorCategory.semantic,
            recognition_criterion="Для ФЗ LHS→RHS из задания 4 есть строки задания 1 с одинаковым LHS и разным RHS.",
            example="Одно значение ключевого атрибута связано с разными значениями зависимого.",
            student_explanation=(
                "Данные контрольного примера нарушают функциональные зависимости: для одного "
                "значения левой части зависимости встречается более одного значения правой части. "
                "Проверьте, что пример согласован с указанными ФЗ."
            ),
            teacher_explanation=(
                "Пример не является корректным экземпляром отношения: нарушена ФЗ. "
                "Строки с одинаковым значением левой части имеют разные значения правой части."
            ),
        ),
        # NEW: EXAMPLE_ALREADY_NORMALIZED
        TypicalError(
            code="EXAMPLE_ALREADY_NORMALIZED",
            title="Контрольный пример уже нормализован",
            description="Число строк в 1НФ не превышает число строк исходного отношения — пример не требует нормализации.",
            task_numbers=(1,),
            category=ErrorCategory.semantic,
            recognition_criterion="len(task3.rows) <= len(task1.rows) при непустых данных.",
            example="Строк в 1НФ столько же или меньше, чем в исходной таблице.",
            student_explanation=(
                "Контрольный пример не содержит повторяющихся групп: число строк в 1НФ "
                "не превышает число строк исходного отношения. Убедитесь, что исходные данные "
                "действительно требуют нормализации."
            ),
            teacher_explanation=(
                "Пример не демонстрирует необходимость нормализации: количество строк "
                "исходного отношения >= количества строк 1НФ."
            ),
        ),
        # NEW: NF1_RELATION_NAME_MISMATCH_TASK1
        TypicalError(
            code="NF1_RELATION_NAME_MISMATCH_TASK1",
            title="Имя 1НФ не совпадает с именем исходного отношения",
            description="Название отношения в задании 3 не совпадает с именем исходного отношения из задания 1.",
            task_numbers=(3,),
            category=ErrorCategory.structural,
            recognition_criterion="normalize(task3.relation) != normalize(task1.relation).",
            example="Задание 1: R1, задание 3: R.",
            student_explanation=(
                "Имя отношения в задании 3 не совпадает с именем исходного отношения "
                "из задания 1. Название таблицы 1НФ должно совпадать с исходным отношением."
            ),
            teacher_explanation=(
                "Кросс-проверка задания 3 и задания 1: имена отношений расходятся."
            ),
        ),
        # NEW: NF1_GROUPS_NOT_ELIMINATED
        TypicalError(
            code="NF1_GROUPS_NOT_ELIMINATED",
            title="1НФ не устраняет повторяющиеся группы",
            description="Число строк в 1НФ не больше числа строк исходного отношения при наличии повторяющихся групп.",
            task_numbers=(3,),
            category=ErrorCategory.semantic,
            recognition_criterion="len(task3.rows) <= len(task1.rows) при наличии групп в задании 2.",
            example="Строк в 1НФ не стало больше, хотя повторяющиеся группы присутствуют.",
            student_explanation=(
                "При устранении повторяющихся групп число строк в таблице должно увеличиться. "
                "Убедитесь, что каждое повторяющееся значение вынесено в отдельную строку."
            ),
            teacher_explanation=(
                "Кросс-проверка: строк в 1НФ <= строк в исходном отношении "
                "при наличии повторяющихся групп. Повторяющиеся группы не раскрыты."
            ),
        ),
        # NEW: PARTIAL_FD_COUNT_MISMATCH
        TypicalError(
            code="PARTIAL_FD_COUNT_MISMATCH",
            title="Число частичных ФЗ не совпадает с ожидаемым",
            description="Число элементарных частичных ФЗ в задании 6 не соответствует числу ФЗ из задания 4 с LHS, пересекающимся с PK.",
            task_numbers=(6,),
            category=ErrorCategory.methodical,
            recognition_criterion="count(task6_elementary) != expected (ФЗ task4: LHS∩PK≠∅, LHS⊄PK).",
            example="Указано 3 частичных ФЗ, ожидалось 2.",
            student_explanation=(
                "Число частичных ФЗ не соответствует ожидаемому. "
                "Частичные ФЗ — это только те зависимости из задания 4, у которых левая "
                "часть является частью первичного ключа (но не всем ключом)."
            ),
            teacher_explanation=(
                "Арифметическая проверка: число элементарных ФЗ в задании 6 "
                "не равно числу ФЗ задания 4 с LHS∩PK≠∅ и LHS⊄PK."
            ),
        ),
        # NEW: PARTIAL_FD_NOT_FROM_KEY_PART
        TypicalError(
            code="PARTIAL_FD_NOT_FROM_KEY_PART",
            title="Частичная ФЗ не зависит от части ключа",
            description="Хотя бы одна ФЗ в задании 6 имеет LHS, ни один атрибут которой не входит в первичный ключ.",
            task_numbers=(6,),
            category=ErrorCategory.semantic,
            recognition_criterion="Для некоторой FD в task6: LHS ∩ pk_attrs = ∅.",
            example="FD D→E в задании 6, но D не входит в PK.",
            student_explanation=(
                "Одна из зависимостей не является частичной: ни один атрибут левой части "
                "не входит в первичный ключ. Частичные ФЗ должны зависеть от части ключа."
            ),
            teacher_explanation=(
                "В задании 6 обнаружена ФЗ, LHS которой не пересекается с PK. "
                "Вероятно, студент отнёс транзитивную зависимость к частичным."
            ),
        ),
        # NEW: TRANSITIVE_FD_COUNT_MISMATCH
        TypicalError(
            code="TRANSITIVE_FD_COUNT_MISMATCH",
            title="Число транзитивных ФЗ не соответствует ожидаемому",
            description="count(task8) != count(task4) - count(task6) по элементарным ФЗ.",
            task_numbers=(8,),
            category=ErrorCategory.methodical,
            recognition_criterion="len(task8_elementary) != len(task4_elementary) - len(task6_elementary).",
            example="task4=5, task6=2, ожидается task8=3, а указано 4.",
            student_explanation=(
                "Число транзитивных ФЗ не соответствует ожидаемому. "
                "Сумма частичных и транзитивных ФЗ должна совпадать с общим числом ФЗ "
                "из задания 4."
            ),
            teacher_explanation=(
                "Арифметическая проверка заданий 4, 6, 8: "
                "count(task4) - count(task6) != count(task8)."
            ),
        ),
        # NEW: FD_DISPLAY_ORDER_WRONG
        TypicalError(
            code="FD_DISPLAY_ORDER_WRONG",
            title="Неверный порядок записи зависимостей в группе",
            description="Первая ФЗ в группе не является объемлющей (должна идти первой).",
            task_numbers=(7, 9),
            category=ErrorCategory.methodical,
            recognition_criterion="В группе первая ФЗ — компонент цепочки, а не объемлющая.",
            example="Записаны A→B, B→C, A→C вместо A→C, A→B, B→C.",
            student_explanation=(
                "Запись зависимостей должна начинаться с объемлющей (внешней) зависимости, "
                "которая является следствием всей цепочки. Например, для цепочки A→B→C "
                "сначала пишется A→C, затем A→B и B→C."
            ),
            teacher_explanation=(
                "Нарушен порядок отображения: объемлющая ФЗ должна быть на первом месте в каждой группе."
            ),
        ),
        # NEW: NESTED_TRANSITIVE_GROUP_COUNT
        TypicalError(
            code="NESTED_TRANSITIVE_GROUP_COUNT",
            title="Неверное число групп вложенных транзитивных ФЗ",
            description="Число групп ФЗ в задании 9 не равно 2 × число транзитивных цепочек из задания 8.",
            task_numbers=(9,),
            category=ErrorCategory.methodical,
            recognition_criterion="groups != 2 × chains.",
            example="2 цепочки → ожидается 4 группы, указано 2.",
            student_explanation=(
                "Для каждой транзитивной цепочки нужно указать две группы: объемлющую "
                "зависимость и составляющие её цепочкой."
            ),
            teacher_explanation=(
                "Число групп в задании 9 не равно 2 × число цепочек из задания 8."
            ),
        ),
        # NEW: SCHEMA_2NF_TABLE_COUNT_MISMATCH
        TypicalError(
            code="SCHEMA_2NF_TABLE_COUNT_MISMATCH",
            title="Неверное число таблиц в 2НФ",
            description="Число таблиц в задании 11 не равно числу частичных ФЗ + 1.",
            task_numbers=(11,),
            category=ErrorCategory.methodical,
            recognition_criterion="count(task11.relations) != count(task6_elementary) + 1.",
            example="2 частичных ФЗ → ожидается 3 таблицы, указано 2.",
            student_explanation=(
                "Число таблиц в 2НФ не соответствует ожидаемому. "
                "Должно быть по одной таблице на каждую частичную ФЗ плюс одна основная таблица."
            ),
            teacher_explanation=(
                "Арифметическая проверка: count(task11.relations) != count(task6_elementary) + 1."
            ),
        ),
        # NEW: SCHEMA_2NF_ROOT_NAME_MISMATCH
        TypicalError(
            code="SCHEMA_2NF_ROOT_NAME_MISMATCH",
            title="Основная таблица 2НФ не имеет имени исходного отношения",
            description="Ни одна таблица в задании 11 не называется так же, как исходное отношение из задания 1.",
            task_numbers=(11,),
            category=ErrorCategory.structural,
            recognition_criterion="normalize(task1.relation) ∉ {normalize(r.name) for r in task11.relations}.",
            example="Исходное отношение R1, но в 2НФ нет таблицы R1.",
            student_explanation=(
                "Основная таблица в 2НФ должна называться так же, как исходное отношение "
                "из задания 1. Ни одна из таблиц не имеет этого имени."
            ),
            teacher_explanation=(
                "Кросс-проверка: имя исходного отношения (задание 1) отсутствует среди "
                "имён таблиц задания 11."
            ),
        ),
        # NEW: SCHEMA_3NF_ROOT_NAME_MISMATCH
        TypicalError(
            code="SCHEMA_3NF_ROOT_NAME_MISMATCH",
            title="Основная таблица 3НФ не имеет имени исходного отношения",
            description="Ни одна таблица в задании 13 не называется так же, как исходное отношение из задания 1.",
            task_numbers=(13,),
            category=ErrorCategory.structural,
            recognition_criterion="normalize(task1.relation) ∉ {normalize(r.name) for r in task13.relations}.",
            example="Исходное отношение R1, но в 3НФ нет таблицы R1.",
            student_explanation=(
                "Основная таблица в 3НФ должна называться так же, как исходное отношение "
                "из задания 1. Ни одна из таблиц не имеет этого имени."
            ),
            teacher_explanation=(
                "Кросс-проверка: имя исходного отношения (задание 1) отсутствует среди "
                "имён таблиц задания 13."
            ),
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
