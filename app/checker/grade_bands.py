from __future__ import annotations

from app.domain.semantic_models import GradeBand, SemanticMark


def semantic_mark_from_fd_sets(
    *,
    ref_elementary_count: int,
    stu_elementary_count: int,
    intersection: int,
) -> GradeBand:
    """
    Шкала по постановке (эталон — множество элементарных ФЗ):
    - ++ : все эталонные ФЗ присутствуют и лишних нет (множества равны)
    - +- : не менее половины эталонных совпало
    - -+ : не менее четверти, но меньше половины
    - -- : меньше четверти

    Для пустого эталона: при пустом ответе — ++; при непустом — оценка по доле «лишнего».
    """
    r = ref_elementary_count
    s = stu_elementary_count
    inter = intersection

    if r == 0 and s == 0:
        return GradeBand(
            SemanticMark.pp,
            "Эталон не содержит элементарных ФЗ; ответ пуст — полное совпадение.",
            "elementary_fd_sets",
        )
    if r == 0 and s > 0:
        return GradeBand(
            SemanticMark.mm,
            "В эталоне нет элементарных ФЗ, в ответе они указаны — несоответствие постановке.",
            "elementary_fd_sets",
        )

    recall = inter / r if r else 0.0
    sets_equal = inter == r == s

    if sets_equal:
        return GradeBand(
            SemanticMark.pp,
            "Множество элементарных ФЗ совпадает с эталонным (полное смысловое совпадение).",
            "elementary_fd_sets",
        )

    if recall >= 0.5:
        mark = SemanticMark.pm
        expl = (
            f"Совпало {inter} из {r} эталонных элементарных ФЗ (не менее половины). "
            "Множества не эквивалентны полностью."
        )
    elif recall >= 0.25:
        mark = SemanticMark.mp
        expl = (
            f"Совпало {inter} из {r} эталонных элементарных ФЗ (меньше половины, не меньше четверти)."
        )
    else:
        mark = SemanticMark.mm
        expl = f"Совпало менее четверти эталонных элементарных ФЗ ({inter} из {r})."

    # Доп. контекст: избыточность ответа
    if s > inter:
        expl += f" В ответе также указано {s - inter} элементарных ФЗ, отсутствующих в эталоне."

    return GradeBand(mark, expl, "elementary_fd_recall")


def semantic_mark_from_status(*, is_correct: bool, is_partial: bool) -> GradeBand:
    """Для заданий без ФЗ: грубое отображение статуса на шкалу (для отображения в UI)."""
    if is_correct:
        return GradeBand(SemanticMark.pp, "Ответ совпадает с эталоном.", "status_map")
    if is_partial:
        return GradeBand(SemanticMark.pm, "Частичное совпадение с эталоном.", "status_map")
    return GradeBand(SemanticMark.mm, "Ответ не совпадает с эталоном.", "status_map")
