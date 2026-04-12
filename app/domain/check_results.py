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
    # Смысловая оценка и типовые ошибки (ВКР: шкала ++/+-/-+/--, каталог)
    semantic_mark: str | None = None
    semantic_mark_explanation: str | None = None
    typical_mistakes: list[dict[str, Any]] = field(default_factory=list)
    semantic_analysis: dict[str, Any] | None = None


@dataclass
class CheckReport:
    task_results: dict[int, TaskCheckResult] = field(default_factory=dict)
    total_score: float = 0.0
    max_score: float = 0.0
    # Аудит: откуда взята привязка к эталону и замечания по структуре книги
    metadata_resolution: str | None = None
    workbook_structure_errors: list[str] = field(default_factory=list)
    semantic_summary: dict[str, Any] | None = None
    check_run_version: str | None = None

    def to_serializable(self) -> dict[str, Any]:
        out: dict[str, Any] = {
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
                    "semantic_mark": v.semantic_mark,
                    "semantic_mark_explanation": v.semantic_mark_explanation,
                    "typical_mistakes": v.typical_mistakes,
                    "semantic_analysis": v.semantic_analysis,
                }
                for k, v in self.task_results.items()
            },
        }
        if self.metadata_resolution:
            out["metadata_resolution"] = self.metadata_resolution
        if self.workbook_structure_errors:
            out["workbook_structure_errors"] = list(self.workbook_structure_errors)
        if self.semantic_summary:
            out["semantic_summary"] = dict(self.semantic_summary)
        if self.check_run_version:
            out["check_run_version"] = self.check_run_version
        return out
