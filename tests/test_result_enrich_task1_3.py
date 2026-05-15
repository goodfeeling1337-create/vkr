from __future__ import annotations

from app.checker.result_enrichment import enrich_task_result
from app.domain.check_results import TaskCheckResult, TaskStatus


def test_enrich_task3_nf1_kind_headers() -> None:
    tr = TaskCheckResult(
        task_number=3,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=["Заголовки столбцов 1НФ не совпадают с эталоном"],
    )
    enrich_task_result(3, tr, ref_payload={}, stu_payload={}, allow_optional_pure_junction=True)
    assert tr.semantic_analysis is not None
    assert tr.semantic_analysis.get("nf1_issue_kind") == "headers"


def test_enrich_task2_group_unknown() -> None:
    tr = TaskCheckResult(
        task_number=2,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=["Неизвестный атрибут в группе: z"],
    )
    enrich_task_result(2, tr, ref_payload={}, stu_payload={}, allow_optional_pure_junction=True)
    assert tr.semantic_analysis is not None
    assert tr.semantic_analysis.get("group_issue") == "unknown_attr"


def test_enrich_sets_human_message_for_correct_answer() -> None:
    tr = TaskCheckResult(
        task_number=6,
        status=TaskStatus.correct,
        score=1.0,
        max_score=1.0,
        errors=[],
    )
    enrich_task_result(
        6,
        tr,
        ref_payload={"fd_lines": ["A -> B"]},
        stu_payload={"fd_lines": ["A -> B"]},
        allow_optional_pure_junction=True,
    )
    assert tr.human_message == "Ответ корректный."


def test_enrich_task2_adds_expected_vs_actual_compare_table() -> None:
    tr = TaskCheckResult(
        task_number=2,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=["Набор групп повторяющихся атрибутов не совпадает с эталоном"],
    )
    enrich_task_result(
        2,
        tr,
        ref_payload={"groups": [["A", "B"]]},
        stu_payload={"groups": [["A", "C"]]},
        allow_optional_pure_junction=True,
    )
    assert tr.human_message
    assert tr.semantic_analysis is not None
    table = tr.semantic_analysis.get("compare_table")
    assert table is not None
    rows = table.get("rows", [])
    assert any(r.get("expected") == "A" for r in rows)
    assert any(r.get("actual") == "C" for r in rows)
    row_c = next(r for r in rows if r.get("actual") == "C")
    assert "compare-attr-wrong" in (row_c.get("actual_html") or "")


def test_enrich_task4_highlights_rhs_attribute_mismatch() -> None:
    tr = TaskCheckResult(
        task_number=4,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=["ФЗ"],
    )
    enrich_task_result(
        4,
        tr,
        ref_payload={"fd_lines": ["A B -> C"]},
        stu_payload={"fd_lines": ["A B -> D"]},
        allow_optional_pure_junction=True,
    )
    rows = tr.semantic_analysis.get("compare_table", {}).get("rows", [])
    assert rows
    r0 = rows[0]
    assert "compare-attr-wrong" in (r0.get("actual_html") or "")
    assert "D" in (r0.get("actual_html") or "")
    assert "compare-attr-wrong" in (r0.get("expected_html") or "")
    assert "C" in (r0.get("expected_html") or "")
