from __future__ import annotations

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel


class TemplateMetadata(BaseModel):
    """Technical metadata embedded in student templates (cells + hidden sheet)."""

    template_id: str
    template_version: int = 1
    # У старых шаблонов в файле может быть число; для новых не используется.
    variant_id: Optional[int] = None
    reference_work_id: int
    reference_version_id: int
    mode: Literal["student_template"] = "student_template"

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> TemplateMetadata:
        return cls.model_validate(data)

    @classmethod
    def from_json_str(cls, s: str) -> TemplateMetadata:
        return cls.from_json_dict(json.loads(s))
