from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.orm import ReferenceWorkVersion, User
from app.repositories import reference as ref_repo


class SubmissionNotAllowed(Exception):
    """Серверная проверка: студент не может сдать работу по этой версии эталона."""

    def __init__(self, message: str, *, http_status: int = 403) -> None:
        super().__init__(message)
        self.http_status = http_status


def ensure_student_may_submit_version(db: Session, user: User, version_id: int) -> ReferenceWorkVersion:
    """
    Жёсткая проверка перед приёмом файла: версия существует, эталон опубликован,
    студенту разрешён этот преподаватель (если задан наставник).
    """
    if user.role.name not in ("student", "admin"):
        raise SubmissionNotAllowed("Только студент может отправить работу.", http_status=403)

    ver = ref_repo.get_version(db, version_id)
    if ver is None:
        raise SubmissionNotAllowed("Эталон не найден.", http_status=404)

    rw = ver.reference_work
    if not rw.is_published:
        raise SubmissionNotAllowed(
            "Нельзя отправить работу по неопубликованному эталону.",
            http_status=403,
        )

    if user.role.name == "student" and user.mentor_teacher_id is not None:
        if rw.teacher_id != user.mentor_teacher_id:
            raise SubmissionNotAllowed(
                "Нет доступа к этому эталону.",
                http_status=403,
            )

    return ver
