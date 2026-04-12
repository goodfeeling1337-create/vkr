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
