from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AttemptFileKind(str, enum.Enum):
    student_upload = "student_upload"
    teacher_review = "teacher_review"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Students may be scoped to a teacher for template listing
    mentor_teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    role: Mapped[Role] = relationship(back_populates="users")
    reference_works: Mapped[list[ReferenceWork]] = relationship(back_populates="teacher")
    student_attempts: Mapped[list[StudentAttempt]] = relationship(
        back_populates="student",
        foreign_keys="StudentAttempt.student_id",
    )


class ReferenceWork(Base):
    __tablename__ = "reference_work"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Режим для студента: training | testing
    scoring_mode: Mapped[str] = mapped_column(String(32), default="training")
    allow_optional_pure_junction: Mapped[bool] = mapped_column(Boolean, default=True)
    # Лимит попыток на студента по этой работе (все версии); None = без лимита
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    teacher: Mapped[User] = relationship(back_populates="reference_works")
    versions: Mapped[list[ReferenceWorkVersion]] = relationship(
        back_populates="reference_work",
        order_by="ReferenceWorkVersion.version_number",
    )

    @property
    def latest_version(self) -> Optional["ReferenceWorkVersion"]:
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.version_number)

    @property
    def latest_version_id(self) -> Optional[int]:
        lv = self.latest_version
        return lv.id if lv else None


class ReferenceWorkVersion(Base):
    __tablename__ = "reference_work_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_work_id: Mapped[int] = mapped_column(ForeignKey("reference_work.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    compiled_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    template_metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reference_work: Mapped[ReferenceWork] = relationship(back_populates="versions")
    task_answers: Mapped[list[ReferenceTaskAnswer]] = relationship(back_populates="version")
    attempts: Mapped[list[StudentAttempt]] = relationship(back_populates="reference_version")


class ReferenceTaskAnswer(Base):
    __tablename__ = "reference_task_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("reference_work_versions.id"), nullable=False)
    task_number: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    version: Mapped[ReferenceWorkVersion] = relationship(back_populates="task_answers")


class StudentAttempt(Base):
    __tablename__ = "student_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reference_version_id: Mapped[int] = mapped_column(
        ForeignKey("reference_work_versions.id"),
        nullable=False,
    )
    submitted_filename: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped[User] = relationship(
        back_populates="student_attempts",
        foreign_keys=[student_id],
    )
    reference_version: Mapped[ReferenceWorkVersion] = relationship(back_populates="attempts")
    files: Mapped[list[StudentAttemptFile]] = relationship(back_populates="attempt")
    check_runs: Mapped[list[CheckRun]] = relationship(back_populates="attempt")
    teacher_review: Mapped[Optional["TeacherReview"]] = relationship(
        back_populates="attempt",
        uselist=False,
    )


class StudentAttemptFile(Base):
    __tablename__ = "student_attempt_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("student_attempts.id"), nullable=False)
    kind: Mapped[AttemptFileKind] = mapped_column(String(32), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)

    attempt: Mapped[StudentAttempt] = relationship(back_populates="files")



class CheckRun(Base):
    __tablename__ = "check_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("student_attempts.id"), nullable=False)
    scoring_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    total_score: Mapped[float] = mapped_column(default=0.0)
    max_score: Mapped[float] = mapped_column(default=0.0)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    attempt: Mapped[StudentAttempt] = relationship(back_populates="check_runs")
    items: Mapped[list[CheckResultItem]] = relationship(back_populates="check_run")


class CheckResultItem(Base):
    __tablename__ = "check_result_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_run_id: Mapped[int] = mapped_column(ForeignKey("check_runs.id"), nullable=False)
    task_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(default=0.0)
    max_score: Mapped[float] = mapped_column(default=0.0)
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    check_run: Mapped[CheckRun] = relationship(back_populates="items")


class TeacherReview(Base):
    __tablename__ = "teacher_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("student_attempts.id"), unique=True, nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attempt: Mapped[StudentAttempt] = relationship(back_populates="teacher_review")
    comments: Mapped[list[TeacherComment]] = relationship(back_populates="review")
    files: Mapped[list[TeacherReviewFile]] = relationship(back_populates="review")


class TeacherComment(Base):
    __tablename__ = "teacher_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("teacher_reviews.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    review: Mapped[TeacherReview] = relationship(back_populates="comments")


class TeacherReviewFile(Base):
    __tablename__ = "teacher_review_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("teacher_reviews.id"), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    review: Mapped[TeacherReview] = relationship(back_populates="files")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UploadedFileRegistry(Base):
    __tablename__ = "uploaded_file_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    storage_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
