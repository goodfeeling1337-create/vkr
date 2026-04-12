from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.orm import TeacherComment, TeacherReview, TeacherReviewFile
from app.services import file_storage

log = logging.getLogger(__name__)


def get_or_create_review(db: Session, attempt_id: int, teacher_id: int) -> TeacherReview:
    r = db.query(TeacherReview).filter(TeacherReview.attempt_id == attempt_id).one_or_none()
    if r:
        if r.teacher_id != teacher_id:
            raise PermissionError("Чужая попытка")
        return r
    r = TeacherReview(attempt_id=attempt_id, teacher_id=teacher_id)
    db.add(r)
    db.flush()
    return r


def add_comment(db: Session, attempt_id: int, teacher_id: int, body: str) -> None:
    rev = get_or_create_review(db, attempt_id, teacher_id)
    db.add(TeacherComment(review_id=rev.id, body=body))
    db.commit()
    log.info("Teacher %s commented attempt %s", teacher_id, attempt_id)


def attach_review_file(
    db: Session,
    attempt_id: int,
    teacher_id: int,
    file_bytes: bytes,
    original_name: str,
) -> None:
    rev = get_or_create_review(db, attempt_id, teacher_id)
    path = file_storage.store_upload(file_bytes, "review", original_name)
    db.add(
        TeacherReviewFile(
            review_id=rev.id,
            storage_path=str(path),
            original_name=original_name,
        ),
    )
    db.commit()
