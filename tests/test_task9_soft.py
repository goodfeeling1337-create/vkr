"""Task 9: simple chain vs nested — compare FD sets, not label."""

from app.checker.checkers.compare import check_task9


def test_simple_chain_same_fd_as_expanded() -> None:
    ref = {"mode": "chains", "fd_lines": ["A -> B", "B -> C", "A -> C"]}
    stu = {"mode": "chains", "fd_lines": ["A -> B", "B -> C", "A -> C"]}
    r = check_task9(ref, stu)
    assert r.status.value == "correct"
