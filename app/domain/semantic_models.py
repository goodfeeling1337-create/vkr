from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


CHECK_RUN_VERSION = "2"


class SemanticMark(str, Enum):
    """Смысловая отметка по шкале постановки (совпадение с эталоном по содержанию ФЗ)."""

    pp = "++"  # полное совпадение множества эталонных ФЗ
    pm = "+-"  # не менее половины эталонных ФЗ присутствует
    mp = "-+"  # не менее четверти, но меньше половины
    mm = "--"  # меньше четверти


class ErrorCategory(str, Enum):
    structural = "structural"
    logical = "logical"
    methodical = "methodical"
    syntactic = "syntactic"


@dataclass
class SemanticComparisonResult:
    """Результат смыслового сравнения (не строкового)."""

    ref_size: int
    stu_size: int
    intersection: int
    recall: float
    precision: float
    jaccard: float
    sets_equal: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref_size": self.ref_size,
            "stu_size": self.stu_size,
            "intersection": self.intersection,
            "recall": self.recall,
            "precision": self.precision,
            "jaccard": self.jaccard,
            "sets_equal": self.sets_equal,
            "notes": list(self.notes),
        }


@dataclass
class GradeBand:
    """Пояснение к выставленной смысловой отметке."""

    mark: SemanticMark
    explanation: str
    match_ratio_basis: str  # например "elementary_fd_recall"


@dataclass
class ReferenceSemanticSnapshot:
    """Каноническое описание эталона для аудита (минимальный срез)."""

    task_number: int
    elementary_fd_count: int | None = None
    payload_kind: str | None = None


@dataclass
class AttemptSemanticSnapshot:
    """Каноническое описание ответа студента для аудита."""

    task_number: int
    elementary_fd_count: int | None = None
    payload_kind: str | None = None
