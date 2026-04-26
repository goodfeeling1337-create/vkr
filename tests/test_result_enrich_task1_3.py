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
