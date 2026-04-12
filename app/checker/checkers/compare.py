from __future__ import annotations

from typing import Any

from app.checker.fd_algebra import group_by_lhs
from app.checker.normalizers import normalize_attribute_name
from app.domain.check_results import TaskCheckResult, TaskStatus


def check_task1(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    errs: list[str] = []
    if normalize_attribute_name(ref.get("relation", "")) != normalize_attribute_name(stu.get("relation", "")):
        errs.append("Название отношения не совпадает")
    rh = [normalize_attribute_name(x) for x in ref.get("headers", [])]
    sh = [normalize_attribute_name(x) for x in stu.get("headers", [])]
    if rh != sh:
        errs.append("Заголовки не совпадают")
    rr = sorted(ref.get("rows", []))
    sr = sorted(stu.get("rows", []))
    if rr != sr:
        errs.append("Набор строк (как мультимножество) не совпадает")
    ok = len(errs) == 0
    return TaskCheckResult(
        1,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
        human_message=None,
    )


def check_task2(ref: dict[str, Any], stu: dict[str, Any], attr_vocab: set[str]) -> TaskCheckResult:
    rg = ref.get("groups", [])
    sg = stu.get("groups", [])
    errs: list[str] = []
    for g in sg:
        for a in g:
            if a not in attr_vocab:
                errs.append(f"Неизвестный атрибут в группе: {a}")
    if sorted(rg) != sorted(sg):
        errs.append("Наборы групп не совпадают")
    ok = len(errs) == 0
    return TaskCheckResult(
        2,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def _key_unique(rows: list[tuple[str, ...]], key_idx: list[int]) -> bool:
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        k = tuple(row[i] for i in key_idx if i < len(row))
        if k in seen:
            return False
        seen.add(k)
    return True


def check_task3(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    errs: list[str] = []
    if [normalize_attribute_name(x) for x in ref.get("headers", [])] != [
        normalize_attribute_name(x) for x in stu.get("headers", [])
    ]:
        errs.append("Заголовки не совпадают")
    rk = [normalize_attribute_name(x) for x in ref.get("key_attributes", [])]
    sk = [normalize_attribute_name(x) for x in stu.get("key_attributes", [])]
    if sorted(rk) != sorted(sk):
        errs.append("Ключевые атрибуты не совпадают")
    rr = ref.get("rows", [])
    sr = stu.get("rows", [])
    if sorted(rr) != sorted(sr):
        errs.append("Строки данных не совпадают (как мультимножество)")
    hdrs = [normalize_attribute_name(x) for x in stu.get("headers", [])]
    key_idx = [i for i, h in enumerate(hdrs) if h in set(sk)]
    if hdrs and key_idx and sr:
        if not _key_unique(sr, key_idx):
            errs.append("Указанный ключ не уникализирует строки таблицы")
    ok = len(errs) == 0
    return TaskCheckResult(
        3,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task4(ref: dict[str, Any], stu: dict[str, Any], vocab: set[str]) -> TaskCheckResult:
    rl = ref.get("fd_lines", [])
    sl = stu.get("fd_lines", [])
    rg = group_by_lhs(rl)
    sg = group_by_lhs(sl)
    errs: list[str] = []
    for lhs, rhs in sg.items():
        for a in lhs:
            if a not in vocab:
                errs.append(f"Левая часть: неизвестный атрибут {a}")
        for a in rhs:
            if a not in vocab:
                errs.append(f"Правая часть: неизвестный атрибут {a}")
    if rg != sg:
        errs.append("Множество функциональных зависимостей не совпадает (после канонизации)")
    ok = len(errs) == 0
    return TaskCheckResult(
        4,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task5(
    ref: dict[str, Any],
    stu: dict[str, Any],
    task3_ref: dict[str, Any] | None,
    task3_stu: dict[str, Any] | None,
) -> TaskCheckResult:
    rp = {normalize_attribute_name(x) for x in ref.get("pk_attributes", [])}
    sp = {normalize_attribute_name(x) for x in stu.get("pk_attributes", [])}
    errs: list[str] = []
    if rp != sp:
        errs.append("Множество атрибутов первичного ключа не совпадает")
    if task3_ref and task3_stu:
        # Soft cross-check: student key should uniquely identify rows in student's table
        hdr = [normalize_attribute_name(x) for x in task3_stu.get("headers", [])]
        rows = task3_stu.get("rows", [])
        idxs = [i for i, h in enumerate(hdr) if h in sp]
        if hdr and idxs and rows:
            if not _key_unique(rows, idxs):
                errs.append("По данным задания 3 выбранный ключ не уникализирует строки")
    ok = len(errs) == 0
    return TaskCheckResult(
        5,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task6(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    rg = group_by_lhs(ref.get("fd_lines", []))
    sg = group_by_lhs(stu.get("fd_lines", []))
    errs: list[str] = []
    if rg != sg:
        errs.append("Каноническое представление частичных ФЗ не совпадает")
    ok = len(errs) == 0
    return TaskCheckResult(
        6,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task7(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    """Compare grouped FDs; levels used only if both present for structural hint."""
    rg = group_by_lhs(ref.get("fd_lines", []))
    sg = group_by_lhs(stu.get("fd_lines", []))
    errs: list[str] = []
    if rg != sg:
        errs.append("Вложенные частичные ФЗ не совпадают (канонически)")
    ok = len(errs) == 0
    return TaskCheckResult(
        7,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task8(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    rg = group_by_lhs(ref.get("fd_lines", []))
    sg = group_by_lhs(stu.get("fd_lines", []))
    ok = rg == sg
    return TaskCheckResult(
        8,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=[] if ok else ["Транзитивные ФЗ не совпадают"],
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task9(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    """Soft: compare elementary FD sets; do not penalize simple chain vs nested if FD sets match."""
    rm = ref.get("mode", "chains")
    sm = stu.get("mode", "chains")
    rfd = ref.get("fd_lines", [])
    sfd = stu.get("fd_lines", [])
    rg = group_by_lhs(rfd)
    sg = group_by_lhs(sfd)
    if rm == "none" and sm == "none":
        ok = True
        errs: list[str] = []
    else:
        ok = rg == sg
        errs = [] if ok else ["Итоговый набор транзитивных ФЗ не совпадает"]
    return TaskCheckResult(
        9,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def _canon_relation_set(rels: list[dict[str, Any]], allow_drop_pure: bool) -> set[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    out: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for r in rels:
        name = normalize_attribute_name(r.get("name", ""))
        attrs = {normalize_attribute_name(a) for a in r.get("attributes", [])}
        keys = {normalize_attribute_name(a) for a in r.get("key_attributes", [])}
        if allow_drop_pure and attrs == keys and len(attrs) >= 2:
            continue
        out.add((name, tuple(sorted(attrs)), tuple(sorted(keys))))
    return out


def check_task11(
    ref: dict[str, Any],
    stu: dict[str, Any],
    allow_optional_pure_junction: bool,
) -> TaskCheckResult:
    rr = ref.get("relations", [])
    sr = stu.get("relations", [])
    rc = _canon_relation_set(rr, allow_optional_pure_junction)
    sc = _canon_relation_set(sr, allow_optional_pure_junction)
    ok = rc == sc
    return TaskCheckResult(
        11,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=[] if ok else ["Схемы отношений 2НФ не совпадают"],
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task13(
    ref: dict[str, Any],
    stu: dict[str, Any],
    allow_optional_pure_junction: bool,
) -> TaskCheckResult:
    rr = ref.get("relations", [])
    sr = stu.get("relations", [])
    rc = _canon_relation_set(rr, allow_optional_pure_junction)
    sc = _canon_relation_set(sr, allow_optional_pure_junction)
    ok = rc == sc
    return TaskCheckResult(
        13,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=[] if ok else ["Схемы отношений 3НФ не совпадают"],
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )
