from app.checker.semantic_compare import compare_elementary_fd_sets


def test_fd_sets_equal():
    lines = ["A -> B", "C -> D"]
    c = compare_elementary_fd_sets(lines, lines)
    assert c.sets_equal is True
    assert c.recall == 1.0


def test_fd_partial_recall():
    ref = ["A -> B", "C -> D"]
    stu = ["A -> B"]
    c = compare_elementary_fd_sets(ref, stu)
    assert c.intersection == 1
    assert c.ref_size == 2
    assert c.recall == 0.5
