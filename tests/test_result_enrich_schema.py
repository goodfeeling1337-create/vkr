from __future__ import annotations

from app.checker.result_enrichment import enrich_task_result
from app.domain.check_results import TaskCheckResult, TaskStatus
from app.domain.semantic_models import SemanticComparisonResult


def test_enrich_task11_sets_schema_gap_kind() -> None:
    tr = TaskCheckResult(
        task_number=11,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=["схема"],
    )
    ref_payload = {"relations": [{"name": "R1", "attrs": ("a",), "key": ("a",)}]}
    stu_payload = {"relations": []}

    def fake_compare(ref: dict, stu: dict, *, allow_optional_pure_junction: bool):
        return SemanticComparisonResult(
            ref_size=1,
            stu_size=0,
            intersection=0,
            recall=0.0,
            precision=1.0,
            jaccard=0.0,
            sets_equal=False,
            notes=[],
        )

    import app.checker.result_enrichment as re

    orig = re.compare_relation_schemas
    re.compare_relation_schemas = fake_compare  # type: ignore[assignment]
    try:
        enrich_task_result(11, tr, ref_payload=ref_payload, stu_payload=stu_payload, allow_optional_pure_junction=True)
    finally:
        re.compare_relation_schemas = orig  # type: ignore[assignment]

    assert tr.semantic_analysis is not None
    assert tr.semantic_analysis.get("schema_normal_form") == "2nf"
    assert tr.semantic_analysis.get("schema_gap_kind") == "incomplete_vs_ref"


def test_enrich_task13_extra_vs_ref() -> None:
    tr = TaskCheckResult(
        task_number=13,
        status=TaskStatus.wrong,
        score=0.0,
        max_score=1.0,
        errors=[],
    )

    def fake_compare(ref: dict, stu: dict, *, allow_optional_pure_junction: bool):
        return SemanticComparisonResult(
            ref_size=1,
            stu_size=2,
            intersection=1,
            recall=1.0,
            precision=0.5,
            jaccard=0.5,
            sets_equal=False,
            notes=[],
        )

    import app.checker.result_enrichment as re

    orig = re.compare_relation_schemas
    re.compare_relation_schemas = fake_compare  # type: ignore[assignment]
    try:
        enrich_task_result(13, tr, ref_payload={"relations": []}, stu_payload={"relations": []}, allow_optional_pure_junction=True)
    finally:
        re.compare_relation_schemas = orig  # type: ignore[assignment]

    assert tr.semantic_analysis is not None
    assert tr.semantic_analysis.get("schema_normal_form") == "3nf"
    assert tr.semantic_analysis.get("schema_gap_kind") == "extra_vs_ref"
