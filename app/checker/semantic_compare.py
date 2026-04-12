from __future__ import annotations

from typing import Any

from app.checker.fd_algebra import elementary_fd_signature, group_by_lhs
from app.checker.checkers.compare import _canon_relation_set
from app.domain.semantic_models import SemanticComparisonResult


def compare_elementary_fd_sets(ref_lines: list[str], stu_lines: list[str]) -> SemanticComparisonResult:
    """Смысловое сравнение множеств элементарных ФЗ (канонический вид)."""
    r = elementary_fd_signature(ref_lines or [])
    s = elementary_fd_signature(stu_lines or [])
    inter = len(r & s)
    union = len(r | s)
    ref_n, stu_n = len(r), len(s)
    recall = inter / ref_n if ref_n else (1.0 if stu_n == 0 else 0.0)
    precision = inter / stu_n if stu_n else (1.0 if ref_n == 0 else 0.0)
    jacc = inter / union if union else 1.0
    return SemanticComparisonResult(
        ref_size=ref_n,
        stu_size=stu_n,
        intersection=inter,
        recall=recall,
        precision=precision,
        jaccard=jacc,
        sets_equal=r == s,
        notes=[],
    )


def compare_task4_grouped_fd(ref_lines: list[str], stu_lines: list[str]) -> SemanticComparisonResult:
    """
    Дополнительная метрика для задания 4: согласованность с группировкой по LHS (как в check_task4).
    Используется в semantic_analysis.notes, основная шкала — по элементарным множествам.
    """
    rg = group_by_lhs(ref_lines or [])
    sg = group_by_lhs(stu_lines or [])
    # Представляем как множество пар (lhs, rhs) для каждого rhs в группе
    r_flat: set[tuple[tuple[str, ...], str]] = set()
    s_flat: set[tuple[tuple[str, ...], str]] = set()
    for lhs, rhs_set in rg.items():
        lhs_t = tuple(sorted(lhs))
        for rhs in rhs_set:
            r_flat.add((lhs_t, rhs))
    for lhs, rhs_set in sg.items():
        lhs_t = tuple(sorted(lhs))
        for rhs in rhs_set:
            s_flat.add((lhs_t, rhs))
    inter = len(r_flat & s_flat)
    union = len(r_flat | s_flat)
    ref_n, stu_n = len(r_flat), len(s_flat)
    recall = inter / ref_n if ref_n else (1.0 if stu_n == 0 else 0.0)
    precision = inter / stu_n if stu_n else (1.0 if ref_n == 0 else 0.0)
    jacc = inter / union if union else 1.0
    return SemanticComparisonResult(
        ref_size=ref_n,
        stu_size=stu_n,
        intersection=inter,
        recall=recall,
        precision=precision,
        jaccard=jacc,
        sets_equal=r_flat == s_flat,
        notes=["grouped_lhs_rhs_pairs"],
    )


def compare_relation_schemas(
    ref: dict[str, Any],
    stu: dict[str, Any],
    *,
    allow_optional_pure_junction: bool,
) -> SemanticComparisonResult:
    """Каноническое сравнение схем отношений (порядок отношений и атрибутов не важен)."""
    rr = ref.get("relations", [])
    sr = stu.get("relations", [])
    rc = _canon_relation_set(rr, allow_optional_pure_junction)
    sc = _canon_relation_set(sr, allow_optional_pure_junction)
    inter = len(rc & sc)
    union = len(rc | sc)
    ref_n, stu_n = len(rc), len(sc)
    recall = inter / ref_n if ref_n else (1.0 if stu_n == 0 else 0.0)
    precision = inter / stu_n if stu_n else (1.0 if ref_n == 0 else 0.0)
    jacc = inter / union if union else 1.0
    return SemanticComparisonResult(
        ref_size=ref_n,
        stu_size=stu_n,
        intersection=inter,
        recall=recall,
        precision=precision,
        jaccard=jacc,
        sets_equal=rc == sc,
        notes=["canonical_relation_set"],
    )
