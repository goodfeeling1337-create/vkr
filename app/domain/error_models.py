from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.domain.semantic_models import ErrorCategory


@dataclass(frozen=True)
class TypicalError:
    """Описание типовой ошибки нормализации (каталог)."""

    code: str
    title: str
    description: str
    task_numbers: tuple[int, ...]
    category: ErrorCategory
    recognition_criterion: str
    example: str
    student_explanation: str
    teacher_explanation: str
    matching_rule: str = ""


@dataclass
class ErrorPattern:
    """Правило сопоставления текста ошибки / контекста с кодом типовой ошибки."""

    code: str
    task_numbers: tuple[int, ...] | None  # None = любое задание
    keywords: tuple[str, ...] = ()
    min_recall: float | None = None
    max_recall: float | None = None


@dataclass
class TypicalMistakeMatch:
    """Сопоставление ответа с записью каталога."""

    code: str
    title: str
    category: str
    confidence: float  # 0..1 эвристическая уверенность
    student_message: str
    teacher_message: str
    matching_rule: str | None = None


@dataclass
class TaskErrorAnalysis:
    """Итог классификации ошибок по одному заданию."""

    task_number: int
    matches: list[TypicalMistakeMatch] = field(default_factory=list)
    raw_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_number": self.task_number,
            "typical_mistakes": [
                {
                    "code": m.code,
                    "title": m.title,
                    "category": m.category,
                    "confidence": m.confidence,
                    "student_message": m.student_message,
                    "teacher_message": m.teacher_message,
                    **({"matching_rule": m.matching_rule} if m.matching_rule else {}),
                }
                for m in self.matches
            ],
            "raw_hints": list(self.raw_hints),
        }


ErrorClassification = Literal["structural", "syntactic", "semantic", "logical", "methodical"]
