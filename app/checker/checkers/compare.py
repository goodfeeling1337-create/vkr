from __future__ import annotations

from typing import Any

from app.checker.fd_algebra import elementary_fd_signature, group_by_lhs
from app.checker.normalizers import normalize_attribute_name
from app.domain.check_results import TaskCheckResult, TaskStatus


def check_task1(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    errs: list[str] = []
    error_kind: str | None = None
    if normalize_attribute_name(ref.get("relation", "")) != normalize_attribute_name(stu.get("relation", "")):
        errs.append("Название исходного отношения не совпадает с эталоном")
        error_kind = "relation_name"
    rh = [normalize_attribute_name(x) for x in ref.get("headers", [])]
    sh = [normalize_attribute_name(x) for x in stu.get("headers", [])]
    if rh != sh:
        errs.append("Заголовки атрибутов не совпадают с эталоном")
        if error_kind is None:
            error_kind = "headers"
    rr = sorted(ref.get("rows", []))
    sr = sorted(stu.get("rows", []))
    if rr != sr:
        errs.append("Набор строк не совпадает с эталоном (мультимножество строк)")
        if error_kind is None:
            error_kind = "rows"
    ok = len(errs) == 0
    result = TaskCheckResult(
        1,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
        human_message=None,
    )
    result.error_kind = error_kind
    return result


def check_task2(ref: dict[str, Any], stu: dict[str, Any], attr_vocab: set[str]) -> TaskCheckResult:
    rg = ref.get("groups", [])
    sg = stu.get("groups", [])
    errs: list[str] = []
    error_kind: str | None = None
    for g in sg:
        for a in g:
            if a not in attr_vocab:
                errs.append(f"Неизвестный атрибут в группе: {a}")
                if error_kind is None:
                    error_kind = "unknown_attr"
    if sorted(rg) != sorted(sg):
        errs.append("Набор групп повторяющихся атрибутов не совпадает с эталоном")
        if error_kind is None:
            error_kind = "groups_mismatch"
    ok = len(errs) == 0
    result = TaskCheckResult(
        2,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )
    result.error_kind = error_kind
    return result


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
    error_kind: str | None = None
    rel_r = normalize_attribute_name(str(ref.get("relation", "") or ""))
    rel_s = normalize_attribute_name(str(stu.get("relation", "") or ""))
    if rel_r and rel_s and rel_r != rel_s:
        errs.append("Название отношения в задании 3 не совпадает с эталоном")
        error_kind = "relation_name"
    # Если в эталоне есть строка с названием, а у студента она опущена — не штрафуем при совпадении таблицы
    if [normalize_attribute_name(x) for x in ref.get("headers", [])] != [
        normalize_attribute_name(x) for x in stu.get("headers", [])
    ]:
        errs.append("Заголовки столбцов 1НФ не совпадают с эталоном")
        if error_kind is None:
            error_kind = "headers"
    rk = [normalize_attribute_name(x) for x in ref.get("key_attributes", [])]
    sk = [normalize_attribute_name(x) for x in stu.get("key_attributes", [])]
    if sorted(rk) != sorted(sk):
        errs.append("Ключевые атрибуты 1НФ не совпадают с эталоном")
        if error_kind is None:
            error_kind = "key_attributes"
    rr = ref.get("rows", [])
    sr = stu.get("rows", [])
    if sorted(rr) != sorted(sr):
        errs.append("Строки данных 1НФ не совпадают с эталоном (мультимножество строк)")
        if error_kind is None:
            error_kind = "rows"
    hdrs = [normalize_attribute_name(x) for x in stu.get("headers", [])]
    key_idx = [i for i, h in enumerate(hdrs) if h in set(sk)]
    if hdrs and key_idx and sr:
        if not _key_unique(sr, key_idx):
            errs.append("Указанный ключ 1НФ не уникализирует строки таблицы (есть дубликаты по ключу)")
            if error_kind is None:
                error_kind = "key_not_unique"
    ok = len(errs) == 0
    result = TaskCheckResult(
        3,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )
    result.error_kind = error_kind
    return result


def check_task4(ref: dict[str, Any], stu: dict[str, Any], vocab: set[str]) -> TaskCheckResult:
    rl = ref.get("fd_lines", [])
    sl = stu.get("fd_lines", [])
    rg = group_by_lhs(rl)
    sg = group_by_lhs(sl)
    errs: list[str] = []
    for lhs, rhs in sg.items():
        for a in lhs:
            if a not in vocab:
                errs.append(f"Левая часть ФЗ: атрибут «{a}» не из словаря задания 1")
        for a in rhs:
            if a not in vocab:
                errs.append(f"Правая часть ФЗ: атрибут «{a}» не из словаря задания 1")
    if rg != sg:
        errs.append(
            "Множество функциональных зависимостей не совпадает с эталоном (канонизация по элементарным ФЗ)",
        )
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
    error_kind: str | None = None
    if rp != sp:
        if sp and rp and sp < rp:
            errs.append("Неполный первичный ключ: не хватает атрибутов по сравнению с эталоном.")
            error_kind = "incomplete"
        elif sp and rp and rp < sp:
            errs.append("Избыточный первичный ключ: лишние атрибуты относительно эталона.")
            error_kind = "redundant"
        else:
            errs.append("Множество атрибутов первичного ключа не совпадает с эталоном.")
            error_kind = "mismatch"
    if task3_ref and task3_stu:
        # Soft cross-check: student key should uniquely identify rows in student's table
        hdr = [normalize_attribute_name(x) for x in task3_stu.get("headers", [])]
        rows = task3_stu.get("rows", [])
        idxs = [i for i, h in enumerate(hdr) if h in sp]
        if hdr and idxs and rows:
            if not _key_unique(rows, idxs):
                errs.append("По данным задания 3 выбранный ключ логически не уникализирует строки (есть дубликаты по ключу).")
                if error_kind is None:
                    error_kind = "not_unique_on_rows"
    ok = len(errs) == 0
    result = TaskCheckResult(
        5,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )
    result.error_kind = error_kind
    return result


def check_task6(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    rr = elementary_fd_signature(ref.get("fd_lines", []))
    sr = elementary_fd_signature(stu.get("fd_lines", []))
    errs: list[str] = []
    if rr != sr:
        errs.append("Множество элементарных частичных ФЗ не совпадает с эталоном (шаг частичных зависимостей)")
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
    """Сравнение по множеству элементарных ФЗ (вложенность отражается в разборе строк)."""
    rr = elementary_fd_signature(ref.get("fd_lines", []))
    sr = elementary_fd_signature(stu.get("fd_lines", []))
    errs: list[str] = []
    if rr != sr:
        errs.append(
            "Множество элементарных ФЗ не совпадает с эталоном (вложенные формы учтены при разборе строк)",
        )
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
    rg = elementary_fd_signature(ref.get("fd_lines", []))
    sg = elementary_fd_signature(stu.get("fd_lines", []))
    ok = rg == sg
    return TaskCheckResult(
        8,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=[] if ok else ["Множество элементарных транзитивных ФЗ не совпадает с эталоном"],
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )


def check_task9(ref: dict[str, Any], stu: dict[str, Any]) -> TaskCheckResult:
    """Сравнение итогового множества элементарных транзитивных ФЗ (режим «Нет» — отдельно)."""
    rm = ref.get("mode", "chains")
    sm = stu.get("mode", "chains")
    rfd = ref.get("fd_lines", [])
    sfd = stu.get("fd_lines", [])
    r_sig = elementary_fd_signature(rfd)
    s_sig = elementary_fd_signature(sfd)
    if rm == "none" and sm == "none":
        ok = True
        errs: list[str] = []
    elif rm == "none" or sm == "none":
        ok = False
        errs = ['Ожидалось согласованное указание «Нет» или набор ФЗ']
    else:
        ok = r_sig == s_sig
        errs = (
            []
            if ok
            else ["Итоговое множество элементарных транзитивных ФЗ (задание 9) не совпадает с эталоном"]
        )
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


def _fmt_canon_relation(t: tuple[str, tuple[str, ...], tuple[str, ...]]) -> str:
    name, attrs, keys = t
    return f"{name}({','.join(attrs)}) key({','.join(keys)})"


def _schema_set_diff_errors(
    ref_rels: list[dict[str, Any]],
    stu_rels: list[dict[str, Any]],
    *,
    allow_optional_pure_junction: bool,
    label: str,
) -> list[str]:
    rc = _canon_relation_set(ref_rels, allow_optional_pure_junction)
    sc = _canon_relation_set(stu_rels, allow_optional_pure_junction)
    if rc == sc:
        return []
    missing = rc - sc
    extra = sc - rc
    errs: list[str] = []
    if missing:
        lim = 12
        items = sorted(missing, key=lambda x: (x[0], x[1], x[2]))[:lim]
        tail = ""
        if len(missing) > lim:
            tail = f" … (всего не хватает или отличается {len(missing)} отнош.)"
        errs.append(
            "Нет в ответе или отличается от эталона ("
            + label
            + "): "
            + "; ".join(_fmt_canon_relation(x) for x in items)
            + tail
        )
    if extra:
        lim = 12
        items = sorted(extra, key=lambda x: (x[0], x[1], x[2]))[:lim]
        tail = ""
        if len(extra) > lim:
            tail = f" … (всего лишних {len(extra)})"
        errs.append(
            "Лишние отношения относительно эталона ("
            + label
            + "): "
            + "; ".join(_fmt_canon_relation(x) for x in items)
            + tail
        )
    return errs if errs else [f"Схема отношений ({label}) не совпадает с эталоном"]


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
    errs: list[str] = []
    if not ok:
        errs = _schema_set_diff_errors(
            rr,
            sr,
            allow_optional_pure_junction=allow_optional_pure_junction,
            label="2НФ",
        )
    return TaskCheckResult(
        11,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
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
    errs: list[str] = []
    if not ok:
        errs = _schema_set_diff_errors(
            rr,
            sr,
            allow_optional_pure_junction=allow_optional_pure_junction,
            label="3НФ",
        )
    return TaskCheckResult(
        13,
        TaskStatus.correct if ok else TaskStatus.wrong,
        1.0 if ok else 0.0,
        1.0,
        errors=errs,
        parsed_answer=stu,
        expected_answer_snapshot=ref,
    )
