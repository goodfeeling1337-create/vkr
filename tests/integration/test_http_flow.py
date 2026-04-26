"""Смоук-тесты HTTP: логин и панель преподавателя."""

from __future__ import annotations

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.integration


def test_login_page_ok(client) -> None:
    r = client.get("/login")
    assert r.status_code == 200
    assert "login" in r.text.lower() or "логин" in r.text.lower()


def test_teacher_login_and_dashboard(client) -> None:
    r = client.post(
        "/login",
        data={"username": "teacher", "password": "teacher"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    r2 = client.get("/teacher", follow_redirects=False)
    assert r2.status_code == 200


def test_anonymous_root_redirects_to_login(client) -> None:
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location") == "/login"


def test_teacher_can_download_student_uploaded_file(client) -> None:
    # Login as teacher.
    r = client.post(
        "/login",
        data={"username": "teacher", "password": "teacher"},
        follow_redirects=False,
    )
    assert r.status_code == 302

    from app.db.session import SessionLocal
    from app.models.orm import AttemptFileKind, ReferenceWork, ReferenceWorkVersion, StudentAttemptFile, User

    db = SessionLocal()
    try:
        teacher = db.execute(select(User).where(User.username == "teacher")).scalar_one_or_none()
        if teacher is None:
            pytest.skip("Пользователь teacher не найден")
        row = db.execute(
            select(StudentAttemptFile.attempt_id)
            .join(StudentAttemptFile.attempt)
            .join(ReferenceWorkVersion, StudentAttemptFile.attempt.reference_version_id == ReferenceWorkVersion.id)
            .join(ReferenceWork, ReferenceWorkVersion.reference_work_id == ReferenceWork.id)
            .where(
                StudentAttemptFile.kind == AttemptFileKind.student_upload.value,
                ReferenceWork.teacher_id == teacher.id,
            )
            .order_by(StudentAttemptFile.id.desc()),
        ).first()
    finally:
        db.close()
    if row is None:
        pytest.skip("Нет попыток с загруженным файлом студента для teacher")

    attempt_id = int(row.attempt_id)
    r2 = client.get(f"/download/attempt/{attempt_id}/student_file", follow_redirects=False)
    assert r2.status_code == 200
    cdisp = (r2.headers.get("content-disposition") or "").lower()
    assert "attachment" in cdisp
