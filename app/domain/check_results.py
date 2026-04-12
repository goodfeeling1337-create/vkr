from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    correct = "correct"
    partial = "partial"
    wrong = "wrong"
    not_checked = "not_checked"
    parse_error = "parse_error"


@dataclass
class TaskCheckResult:
    task_number: int
    status: TaskStatus
    score: float
    max_score: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parsed_answer: Any = None
    expected_answer_snapshot: Any = None
    human_message: str | None = None


@dataclass
class CheckReport:
    task_results: dict[int, TaskCheckResult] = field(default_factory=dict)
    total_score: float = 0.0
    max_score: float = 0.0

    def to_serializable(self) -> dict[str, Any]:
        return {
            "total_score": self.total_score,
            "max_score": self.max_score,
            "tasks": {
                str(k): {
                    "status": v.status.value,
                    "score": v.score,
                    "max_score": v.max_score,
                    "errors": v.errors,
                    "warnings": v.warnings,
                    "parsed_answer": v.parsed_answer,
                    "expected_answer_snapshot": v.expected_answer_snapshot,
                    "human_message": v.human_message,
                }
                for k, v in self.task_results.items()
            },
        }
