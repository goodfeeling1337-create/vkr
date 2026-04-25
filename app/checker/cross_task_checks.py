"""
Cross-task consistency checks that require data from multiple task answers.
Called once after all individual tasks have been checked and enriched.
Each check appends entries to TaskCheckResult.typical_mistakes directly.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.checker.error_catalog import NormalizationErrorCatalog
from app.checker.fd_algebra import elementary_fd_signature, split_elementary_from_line
from app.checker.normalizers import normalize_attribute_name
from app.domain.check_results import CheckReport, TaskCheckResult, TaskStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parsed(report: CheckReport, task_n: int) -> dict[str, Any] | None:
    """Return parsed_answer for task_n if the task was not a parse error."""
    tr = report.task_results.get(task_n)
    if tr is None or tr.status == TaskStatus.parse_error:
        return None
    return tr.parsed_answer if isinstance(tr.parsed_answer, dict) else None


def _tr(report: CheckReport, task_n: int) -> TaskCheckResult | None:
    return report.task_results.get(task_n)


def _add_mistake(
    tr: TaskCheckResult,
    code: str,
    confidence: float,
    teacher_msg: str,
    student_msg: str | None = None,
) -> None:
    """Append a TypicalMistakeMatch dict to tr.typical_mistakes (deduplicates by code)."""
    existing_codes = {m.get("code") for m in tr.typical_mistakes}
    if code in existing_codes:
        return
    te = NormalizationErrorCatalog.get(code)
    if te is None:
        return
    tr.typical_mistakes.append({
        "code": te.code,
        "title": te.title,
        "category": te.category.value,
        "confidence": confidence,
        "student_message": student_msg if student_msg is not None else te.student_explanation,
        "teacher_message": teacher_msg,
    })


# ---------------------------------------------------------------------------
# NEW: EXAMPLE_VIOLATES_FD  (task 1 vs task 4)
# ---------------------------------------------------------------------------

def _check_example_violates_fd(report: CheckReport) -> None:
    task1 = _parsed(report, 1)
    task4 = _parsed(report, 4)
    if not task1 or not task4:
        return

    headers = [normalize_attribute_name(h) for h in task1.get("headers", [])]
    rows = task1.get("rows", [])
    fd_lines = task4.get("fd_lines", [])
    if not headers or not rows or not fd_lines:
        return

    # Group elementary FDs by LHS for efficient checking
    lhs_groups: dict[frozenset, set[str]] = defaultdict(set)
    for line in fd_lines:
        for fd in split_elementary_from_line(line):
            lhs_groups[fd.lhs].add(fd.rhs)

    for lhs_frozen, rhs_set in lhs_groups.items():
        lhs_idx = [i for i, h in enumerate(headers) if h in lhs_frozen]
        rhs_idx = [i for i, h in enumerate(headers) if h in rhs_set]
        if not lhs_idx or not rhs_idx:
            continue

        seen: dict[tuple, tuple] = {}
        violation_lhs: frozenset | None = None
        violation_rhs: set | None = None
        for row in rows:
            lhs_key = tuple(row[i] for i in lhs_idx if i < len(row))
            rhs_val = tuple(row[i] for i in rhs_idx if i < len(row))
            if lhs_key in seen:
                if seen[lhs_key] != rhs_val:
                    violation_lhs = lhs_frozen
                    violation_rhs = rhs_set
                    break
            else:
                seen[lhs_key] = rhs_val

        if violation_lhs is not None:
            lhs_str = ",".join(sorted(violation_lhs))
            rhs_str = ",".join(sorted(violation_rhs))  # type: ignore[arg-type]
            result = _tr(report, 1)
            if result:
                _add_mistake(
                    result,
                    "EXAMPLE_VIOLATES_FD",
                    0.9,
                    teacher_msg=(
                        f"Пример не является корректным экземпляром отношения: нарушена "
                        f"ФЗ {{{lhs_str}}}→{{{rhs_str}}}. Строки с одинаковым {{{lhs_str}}} "
                        f"имеют разные значения {{{rhs_str}}}."
                    ),
                )
            return  # report first violation only


# ---------------------------------------------------------------------------
# NEW: EXAMPLE_ALREADY_NORMALIZED  (task 1 vs task 3)
# ---------------------------------------------------------------------------

def _check_example_already_normalized(report: CheckReport) -> None:
    task1 = _parsed(report, 1)
    task3 = _parsed(report, 3)
    if not task1 or not task3:
        return

    n1 = len(task1.get("rows", []))
    n3 = len(task3.get("rows", []))
    if n1 <= 0 or n3 <= 0:
        return

    if n3 <= n1:
        result = _tr(report, 1)
        if result:
            _add_mistake(
                result,
                "EXAMPLE_ALREADY_NORMALIZED",
                0.8,
                teacher_msg=(
                    f"Пример не демонстрирует необходимость нормализации: количество строк "
                    f"исходного отношения ({n1}) >= количества строк 1НФ ({n3})."
                ),
                student_msg=(
                    f"Контрольный пример не содержит повторяющихся групп: число строк в 1НФ "
                    f"({n3}) не превышает число строк исходного отношения ({n1}). "
                    "Убедитесь, что исходные данные действительно требуют нормализации."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: NF1_RELATION_NAME_MISMATCH_TASK1  (task 3 vs task 1)
# ---------------------------------------------------------------------------

def _check_nf1_relation_name_mismatch_task1(report: CheckReport) -> None:
    task1 = _parsed(report, 1)
    task3 = _parsed(report, 3)
    if not task1 or not task3:
        return

    name1 = normalize_attribute_name(str(task1.get("relation", "") or ""))
    name3 = normalize_attribute_name(str(task3.get("relation", "") or ""))
    if not name1 or not name3:
        return

    if name1 != name3:
        result = _tr(report, 3)
        if result:
            _add_mistake(
                result,
                "NF1_RELATION_NAME_MISMATCH_TASK1",
                0.88,
                teacher_msg=(
                    f"Кросс-проверка задания 3 и задания 1: имена отношений расходятся "
                    f"(\"{name3}\" vs \"{name1}\")."
                ),
                student_msg=(
                    f"Имя отношения в задании 3 (\"{name3}\") не совпадает с именем исходного "
                    f"отношения из задания 1 (\"{name1}\"). Название таблицы 1НФ должно совпадать "
                    "с исходным отношением."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: NF1_GROUPS_NOT_ELIMINATED  (task 3 vs task 1 + task 2)
# ---------------------------------------------------------------------------

def _check_nf1_groups_not_eliminated(report: CheckReport) -> None:
    task1 = _parsed(report, 1)
    task2 = _parsed(report, 2)
    task3 = _parsed(report, 3)
    if not task1 or not task2 or not task3:
        return

    # Only check if task2 contains at least one non-empty group
    groups = task2.get("groups", [])
    has_groups = any(len(g) > 0 for g in groups)
    if not has_groups:
        return

    n1 = len(task1.get("rows", []))
    n3 = len(task3.get("rows", []))
    if n1 <= 0 or n3 <= 0:
        return

    if n3 <= n1:
        result = _tr(report, 3)
        if result:
            _add_mistake(
                result,
                "NF1_GROUPS_NOT_ELIMINATED",
                0.85,
                teacher_msg=(
                    f"Кросс-проверка: строк в 1НФ ({n3}) <= строк в исходном отношении ({n1}) "
                    "при наличии повторяющихся групп. Повторяющиеся группы не раскрыты."
                ),
                student_msg=(
                    f"При устранении повторяющихся групп число строк в таблице должно увеличиться. "
                    f"Сейчас строк в 1НФ ({n3}) не больше, чем в исходном отношении ({n1}). "
                    "Убедитесь, что каждое повторяющееся значение вынесено в отдельную строку."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: PARTIAL_FD_COUNT_MISMATCH  (task 6 vs task 4 + task 5)
# ---------------------------------------------------------------------------

def _check_partial_fd_count_mismatch(report: CheckReport) -> None:
    task4 = _parsed(report, 4)
    task5 = _parsed(report, 5)
    task6 = _parsed(report, 6)
    if not task4 or not task5 or not task6:
        return

    pk_attrs = {normalize_attribute_name(x) for x in task5.get("pk_attributes", [])}
    if not pk_attrs:
        return

    task4_sig = elementary_fd_signature(task4.get("fd_lines", []))
    # Count FDs from task4 where LHS ∩ pk_attrs ≠ ∅ and LHS ⊄ pk_attrs
    expected = sum(
        1
        for lhs_tuple, _rhs in task4_sig
        if set(lhs_tuple) & pk_attrs and not (set(lhs_tuple) <= pk_attrs)
    )

    task6_sig = elementary_fd_signature(task6.get("fd_lines", []))
    actual = len(task6_sig)

    if actual != expected:
        result = _tr(report, 6)
        if result:
            _add_mistake(
                result,
                "PARTIAL_FD_COUNT_MISMATCH",
                0.82,
                teacher_msg=(
                    f"Арифметическая проверка: задание 6 содержит {actual} элементарных ФЗ, "
                    f"ожидается {expected} (ФЗ задания 4, LHS∩PK≠∅, LHS⊄PK)."
                ),
                student_msg=(
                    f"Число частичных ФЗ ({actual}) не соответствует ожидаемому ({expected}). "
                    "Частичные ФЗ — это только те зависимости из задания 4, у которых левая "
                    "часть является частью первичного ключа (но не всем ключом)."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: PARTIAL_FD_NOT_FROM_KEY_PART  (task 6 vs task 5)
# ---------------------------------------------------------------------------

def _check_partial_fd_not_from_key_part(report: CheckReport) -> None:
    task5 = _parsed(report, 5)
    task6 = _parsed(report, 6)
    if not task5 or not task6:
        return

    pk_attrs = {normalize_attribute_name(x) for x in task5.get("pk_attributes", [])}
    if not pk_attrs:
        return

    task6_sig = elementary_fd_signature(task6.get("fd_lines", []))
    result = _tr(report, 6)
    if result is None:
        return

    for lhs_tuple, rhs in task6_sig:
        lhs_set = set(lhs_tuple)
        if not (lhs_set & pk_attrs):
            lhs_str = ",".join(sorted(lhs_set))
            _add_mistake(
                result,
                "PARTIAL_FD_NOT_FROM_KEY_PART",
                0.87,
                teacher_msg=(
                    f"В задании 6 обнаружена ФЗ «{{{lhs_str}}}→{rhs}», LHS которой не "
                    f"пересекается с PK {{{','.join(sorted(pk_attrs))}}}. "
                    "Вероятно, студент отнёс транзитивную зависимость к частичным."
                ),
                student_msg=(
                    f"Зависимость «{{{lhs_str}}}→{rhs}» не является частичной: ни один "
                    "атрибут левой части не входит в первичный ключ. "
                    "Частичные ФЗ должны зависеть от части ключа."
                ),
            )
            return  # report first violation only


# ---------------------------------------------------------------------------
# NEW: TRANSITIVE_FD_COUNT_MISMATCH  (task 8 vs task 4 + task 6)
# ---------------------------------------------------------------------------

def _check_transitive_fd_count_mismatch(report: CheckReport) -> None:
    task4 = _parsed(report, 4)
    task6 = _parsed(report, 6)
    task8 = _parsed(report, 8)
    if not task4 or not task6 or not task8:
        return

    t4 = len(elementary_fd_signature(task4.get("fd_lines", [])))
    t6 = len(elementary_fd_signature(task6.get("fd_lines", [])))
    t8 = len(elementary_fd_signature(task8.get("fd_lines", [])))

    if t4 == 0:
        return

    expected = t4 - t6
    if expected < 0:
        return  # task6 count exceeds task4 — covered by PARTIAL_FD_COUNT_MISMATCH

    if t8 != expected:
        result = _tr(report, 8)
        if result:
            _add_mistake(
                result,
                "TRANSITIVE_FD_COUNT_MISMATCH",
                0.82,
                teacher_msg=(
                    f"Арифметическая проверка заданий 4, 6, 8: "
                    f"count(task4)={t4} − count(task6)={t6} = {expected}, а не {t8}."
                ),
                student_msg=(
                    f"Число транзитивных ФЗ ({t8}) не соответствует ожидаемому ({expected}). "
                    "Сумма частичных и транзитивных ФЗ должна совпадать с общим числом ФЗ "
                    "из задания 4."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: FD_DISPLAY_ORDER_WRONG  (task 7 and task 9)
# ---------------------------------------------------------------------------

def _check_fd_display_order_wrong(report: CheckReport) -> None:
    _check_fd_display_order_task7(report)
    _check_fd_display_order_task9(report)


def _check_fd_display_order_task7(report: CheckReport) -> None:
    """Task 7: use 'levels' to detect wrong group ordering."""
    task7 = _parsed(report, 7)
    if not task7:
        return

    fd_lines = task7.get("fd_lines", [])
    levels = task7.get("levels", [])
    if not fd_lines or not levels or len(fd_lines) != len(levels):
        return

    # Only check if there is actual indentation (some level > 0)
    if not any(lv > 0 for lv in levels):
        return

    # Within each group (delimited by level-0 entries), the first FD must be
    # at level 0. If we find a level-0 FD after level->0 FDs (i.e., it appears
    # inside an already-started group), flag it.
    # Simple heuristic: if levels[0] > 0, the very first FD is not the outer one.
    if levels[0] > 0:
        result = _tr(report, 7)
        if result:
            _add_mistake(
                result,
                "FD_DISPLAY_ORDER_WRONG",
                0.78,
                teacher_msg=(
                    "Нарушен порядок отображения в задании 7: первая ФЗ в группе "
                    "является компонентом (индентация > 0), а не объемлющей. "
                    "Ожидается: объемлющая ФЗ на первом месте в каждой группе."
                ),
            )
        return

    # Check subsequent groups: after a sequence of higher-level lines,
    # if we encounter another level-0 line that's preceded by higher-level lines —
    # that's a new group starting correctly. But if within a group we see a level-0
    # entry preceded by higher-level entries, that would be wrong.
    # Detection: find positions where levels[i] < levels[i-1] and levels[i] == 0
    # but levels[i-2] (or some earlier) was also 0 — meaning the previous group
    # ended but then the wrapping FD of the *current* group came after its components.
    in_group_has_high = False
    for i in range(1, len(levels)):
        if levels[i - 1] == 0:
            in_group_has_high = False
        elif levels[i - 1] > 0:
            in_group_has_high = True
        if levels[i] == 0 and in_group_has_high:
            # A new group's outer FD came after some inner FDs of previous group
            # which means the previous group's outer FD may have come after its components
            result = _tr(report, 7)
            if result:
                _add_mistake(
                    result,
                    "FD_DISPLAY_ORDER_WRONG",
                    0.75,
                    teacher_msg=(
                        "Нарушен порядок отображения в задании 7: найдена группа, в которой "
                        "объемлющая ФЗ (уровень 0) следует после компонентов. "
                        "Ожидается: объемлющая ФЗ на первом месте в каждой группе."
                    ),
                )
            return


def _check_fd_display_order_task9(report: CheckReport) -> None:
    """Task 9: detect wrapping FD appearing after its components."""
    task9 = _parsed(report, 9)
    if not task9:
        return
    if task9.get("mode") != "chains":
        return

    fd_lines = task9.get("fd_lines", [])
    if len(fd_lines) < 3:
        return

    # Parse all elementary FDs with their line position (index in fd_lines)
    fds_with_pos: list[tuple[frozenset, str, int]] = []
    for i, line in enumerate(fd_lines):
        for fd in split_elementary_from_line(line):
            fds_with_pos.append((fd.lhs, fd.rhs, i))

    if not fds_with_pos:
        return

    # Build position map: (lhs, rhs) → minimum line index
    fd_min_pos: dict[tuple[frozenset, str], int] = {}
    for lhs, rhs, pos in fds_with_pos:
        key = (lhs, rhs)
        if key not in fd_min_pos or pos < fd_min_pos[key]:
            fd_min_pos[key] = pos

    # For each pair A→B and B→C, check if A→C exists and appears AFTER them
    for lhs_a, rhs_b, pos_ab in fds_with_pos:
        for lhs_b, rhs_c, pos_bc in fds_with_pos:
            if lhs_b != frozenset({rhs_b}):
                continue  # B must be the sole LHS of the second FD
            key_ac = (lhs_a, rhs_c)
            if key_ac not in fd_min_pos:
                continue
            pos_ac = fd_min_pos[key_ac]
            # Wrapping A→C should come BEFORE A→B and B→C
            if pos_ac > pos_ab or pos_ac > pos_bc:
                result = _tr(report, 9)
                if result:
                    lhs_a_str = ",".join(sorted(lhs_a))
                    _add_mistake(
                        result,
                        "FD_DISPLAY_ORDER_WRONG",
                        0.78,
                        teacher_msg=(
                            f"Нарушен порядок отображения в задании 9: объемлющая ФЗ "
                            f"{{{lhs_a_str}}}→{rhs_c} записана после составляющих цепочку зависимостей. "
                            "Ожидается: объемлющая ФЗ на первом месте в каждой группе."
                        ),
                    )
                return  # report first violation only


# ---------------------------------------------------------------------------
# NEW: NESTED_TRANSITIVE_GROUP_COUNT  (task 9 vs task 8)
# ---------------------------------------------------------------------------

def _count_chain_starts(fd_lines: list[str]) -> int:
    """
    Count transitive chain 'starts' in fd_lines.
    A start attribute appears in LHS but not in any RHS — it initiates a chain.
    Each distinct start with a non-trivial path counts as one chain.
    """
    all_lhs_attrs: set[str] = set()
    all_rhs_attrs: set[str] = set()
    for line in fd_lines:
        for fd in split_elementary_from_line(line):
            for a in fd.lhs:
                all_lhs_attrs.add(a)
            all_rhs_attrs.add(fd.rhs)
    # Intermediates: appear in both LHS and RHS → each intermediate = 1 chain
    intermediates = all_lhs_attrs & all_rhs_attrs
    return len(intermediates)


def _count_wrapping_fds(fd_lines: list[str]) -> int:
    """
    Count FDs in fd_lines that can be derived from other FDs by transitivity.
    A→C is a wrapper if A→B and B→C both exist in the same set.
    """
    # Build elementary set for fast lookup
    fd_set: set[tuple[frozenset, str]] = set()
    all_fds: list[tuple[frozenset, str]] = []
    for line in fd_lines:
        for fd in split_elementary_from_line(line):
            fd_set.add((fd.lhs, fd.rhs))
            all_fds.append((fd.lhs, fd.rhs))

    count = 0
    seen_wrappers: set[tuple[frozenset, str]] = set()
    for lhs_a, rhs_b in all_fds:
        # Check if lhs_a → rhs_b can be derived: find A→X, X→rhs_b
        # i.e., lhs_a → some_intermediate → rhs_b
        for lhs_b, rhs_c in all_fds:
            if lhs_b == frozenset({rhs_b}):
                # A→B and B→C exist, check if A→C is in the set
                key_ac = (lhs_a, rhs_c)
                if key_ac in fd_set and key_ac not in seen_wrappers:
                    seen_wrappers.add(key_ac)
                    count += 1
    return count


def _check_nested_transitive_group_count(report: CheckReport) -> None:
    task8 = _parsed(report, 8)
    task9 = _parsed(report, 9)
    if not task8 or not task9:
        return
    if task9.get("mode") != "chains":
        return

    task8_fd_lines = task8.get("fd_lines", [])
    task9_fd_lines = task9.get("fd_lines", [])
    if not task8_fd_lines or not task9_fd_lines:
        return

    # Chains from task8 = number of intermediate nodes
    chains = _count_chain_starts(task8_fd_lines)
    if chains == 0:
        return

    # Groups in task9: each chain contributes 2 groups (wrapping + components)
    # We approximate actual groups by counting wrapping FDs in task9
    wrappings_in_task9 = _count_wrapping_fds(task9_fd_lines)

    expected_groups = 2 * chains
    actual_groups = 2 * wrappings_in_task9

    if actual_groups != expected_groups:
        result = _tr(report, 9)
        if result:
            _add_mistake(
                result,
                "NESTED_TRANSITIVE_GROUP_COUNT",
                0.75,
                teacher_msg=(
                    f"Число групп в задании 9 ({actual_groups}) не равно "
                    f"2 × число цепочек ({chains} × 2 = {expected_groups})."
                ),
                student_msg=(
                    f"Для каждой транзитивной цепочки нужно указать две группы: объемлющую "
                    f"зависимость и составляющие её цепочкой. Сейчас групп {actual_groups}, "
                    f"ожидается {expected_groups}."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: SCHEMA_2NF_TABLE_COUNT_MISMATCH  (task 11 vs task 6)
# ---------------------------------------------------------------------------

def _check_schema_2nf_table_count_mismatch(report: CheckReport) -> None:
    task6 = _parsed(report, 6)
    task11 = _parsed(report, 11)
    if not task6 or not task11:
        return

    task6_sig = elementary_fd_signature(task6.get("fd_lines", []))
    expected = len(task6_sig) + 1

    relations = task11.get("relations", [])
    actual = len(relations)

    if actual != expected:
        result = _tr(report, 11)
        if result:
            _add_mistake(
                result,
                "SCHEMA_2NF_TABLE_COUNT_MISMATCH",
                0.80,
                teacher_msg=(
                    f"Арифметическая проверка: count(task11.relations)={actual}, "
                    f"ожидается count(task6)+1={expected}."
                ),
                student_msg=(
                    f"Число таблиц в 2НФ ({actual}) не соответствует ожидаемому ({expected}). "
                    "Должно быть по одной таблице на каждую частичную ФЗ плюс одна основная таблица."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: SCHEMA_2NF_ROOT_NAME_MISMATCH  (task 11 vs task 1)
# ---------------------------------------------------------------------------

def _check_schema_2nf_root_name_mismatch(report: CheckReport) -> None:
    task1 = _parsed(report, 1)
    task11 = _parsed(report, 11)
    if not task1 or not task11:
        return

    root_name = normalize_attribute_name(str(task1.get("relation", "") or ""))
    if not root_name:
        return

    relation_names = {
        normalize_attribute_name(str(r.get("name", "")))
        for r in task11.get("relations", [])
    }

    if root_name not in relation_names:
        result = _tr(report, 11)
        if result:
            _add_mistake(
                result,
                "SCHEMA_2NF_ROOT_NAME_MISMATCH",
                0.85,
                teacher_msg=(
                    f"Кросс-проверка: имя «{root_name}» (задание 1) отсутствует среди "
                    "имён таблиц задания 11."
                ),
                student_msg=(
                    f"Основная таблица в 2НФ должна называться так же, как исходное отношение "
                    f"из задания 1 («{root_name}»). Ни одна из таблиц не имеет этого имени."
                ),
            )


# ---------------------------------------------------------------------------
# NEW: SCHEMA_3NF_ROOT_NAME_MISMATCH  (task 13 vs task 1)
# ---------------------------------------------------------------------------

def _check_schema_3nf_root_name_mismatch(report: CheckReport) -> None:
    task1 = _parsed(report, 1)
    task13 = _parsed(report, 13)
    if not task1 or not task13:
        return

    root_name = normalize_attribute_name(str(task1.get("relation", "") or ""))
    if not root_name:
        return

    relation_names = {
        normalize_attribute_name(str(r.get("name", "")))
        for r in task13.get("relations", [])
    }

    if root_name not in relation_names:
        result = _tr(report, 13)
        if result:
            _add_mistake(
                result,
                "SCHEMA_3NF_ROOT_NAME_MISMATCH",
                0.85,
                teacher_msg=(
                    f"Кросс-проверка: имя «{root_name}» (задание 1) отсутствует среди "
                    "имён таблиц задания 13."
                ),
                student_msg=(
                    f"Основная таблица в 3НФ должна называться так же, как исходное отношение "
                    f"из задания 1 («{root_name}»). Ни одна из таблиц не имеет этого имени."
                ),
            )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_cross_task_checks(report: CheckReport) -> None:
    """
    Run all cross-task consistency checks.
    Called after individual task checks and enrichment, before finalize_report_semantics.
    Appends TypicalMistakeMatch dicts to relevant TaskCheckResult.typical_mistakes.
    """
    # NEW: EXAMPLE_VIOLATES_FD
    _check_example_violates_fd(report)
    # NEW: EXAMPLE_ALREADY_NORMALIZED
    _check_example_already_normalized(report)
    # NEW: NF1_RELATION_NAME_MISMATCH_TASK1
    _check_nf1_relation_name_mismatch_task1(report)
    # NEW: NF1_GROUPS_NOT_ELIMINATED
    _check_nf1_groups_not_eliminated(report)
    # NEW: PARTIAL_FD_COUNT_MISMATCH
    _check_partial_fd_count_mismatch(report)
    # NEW: PARTIAL_FD_NOT_FROM_KEY_PART
    _check_partial_fd_not_from_key_part(report)
    # NEW: TRANSITIVE_FD_COUNT_MISMATCH
    _check_transitive_fd_count_mismatch(report)
    # NEW: FD_DISPLAY_ORDER_WRONG (tasks 7 and 9)
    _check_fd_display_order_wrong(report)
    # NEW: NESTED_TRANSITIVE_GROUP_COUNT
    _check_nested_transitive_group_count(report)
    # NEW: SCHEMA_2NF_TABLE_COUNT_MISMATCH
    _check_schema_2nf_table_count_mismatch(report)
    # NEW: SCHEMA_2NF_ROOT_NAME_MISMATCH
    _check_schema_2nf_root_name_mismatch(report)
    # NEW: SCHEMA_3NF_ROOT_NAME_MISMATCH
    _check_schema_3nf_root_name_mismatch(report)
