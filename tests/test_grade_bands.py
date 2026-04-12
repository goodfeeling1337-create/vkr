from app.checker.grade_bands import semantic_mark_from_fd_sets
from app.domain.semantic_models import SemanticMark


def test_pp_equal_sets():
    g = semantic_mark_from_fd_sets(ref_elementary_count=3, stu_elementary_count=3, intersection=3)
    assert g.mark == SemanticMark.pp


def test_pm_half_recall():
    g = semantic_mark_from_fd_sets(ref_elementary_count=4, stu_elementary_count=4, intersection=2)
    assert g.mark == SemanticMark.pm


def test_mp_quarter_to_half():
    g = semantic_mark_from_fd_sets(ref_elementary_count=4, stu_elementary_count=4, intersection=1)
    assert g.mark == SemanticMark.mp


def test_mm_below_quarter():
    g = semantic_mark_from_fd_sets(ref_elementary_count=10, stu_elementary_count=10, intersection=1)
    assert g.mark == SemanticMark.mm
