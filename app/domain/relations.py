from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RelationSchema:
    name: str
    attributes: frozenset[str]
    key_attributes: frozenset[str]

    def is_pure_junction(self) -> bool:
        return self.attributes == self.key_attributes and len(self.attributes) >= 2


@dataclass
class RelationSchemaSet:
    relations: set[RelationSchema] = field(default_factory=set)
