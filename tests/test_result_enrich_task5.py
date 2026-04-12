from __future__ import annotations

from app.checker.result_enrichment import enrich_task_result
from app.domain.check_results import TaskCheckResult, TaskStatus


def test_enrich_task5_sets_pk_kind_incomplete() -> None:
    tr = TaskCheckResult(
        task_number=5,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=["Неполный первичный ключ: не хватает атрибутов по сравнению с эталоном."],
    )
    enrich_task_result(
        5,
        tr,
        ref_payload={"pk_attributes": ["a"]},
        stu_payload={"pk_attributes": []},
        allow_optional_pure_junction=True,
    )
    assert tr.semantic_analysis is not None
    assert tr.semantic_analysis.get("pk_kind") == "incomplete"
