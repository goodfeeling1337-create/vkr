"""Серверная политика: студент и версия эталона."""

from unittest.mock import MagicMock

import pytest

from app.services.reference_access import SubmissionNotAllowed, ensure_student_may_submit_version


def test_rejects_unpublished(monkeypatch: pytest.MonkeyPatch) -> None:
    db = MagicMock()
    user = MagicMock()
    user.role.name = "student"
    user.mentor_teacher_id = 10

    ver = MagicMock()
    ver.reference_work.is_published = False
    ver.reference_work.teacher_id = 10

    monkeypatch.setattr(
        "app.services.reference_access.ref_repo.get_version",
        lambda _db, _vid: ver,
    )

    with pytest.raises(SubmissionNotAllowed) as ei:
        ensure_student_may_submit_version(db, user, 1)
    assert "неопубликован" in str(ei.value).lower()


def test_rejects_wrong_mentor(monkeypatch: pytest.MonkeyPatch) -> None:
    db = MagicMock()
    user = MagicMock()
    user.role.name = "student"
    user.mentor_teacher_id = 1

    ver = MagicMock()
    ver.reference_work.is_published = True
    ver.reference_work.teacher_id = 99

    monkeypatch.setattr(
        "app.services.reference_access.ref_repo.get_version",
        lambda _db, _vid: ver,
    )

    with pytest.raises(SubmissionNotAllowed):
        ensure_student_may_submit_version(db, user, 1)
