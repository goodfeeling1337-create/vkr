from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyChain:
    """Linear chain A -> B -> C -> D as ordered attributes."""

    attrs: list[str] = field(default_factory=list)

    def normalized_tuple(self) -> tuple[str, ...]:
        return tuple(a.strip() for a in self.attrs if a.strip())


@dataclass
class NestedPartialFD:
    """Task 7: nested LHS groups with RHS names at leaves."""

    lhs_groups: tuple["NestedPartialFD | frozenset[str]", ...]
    rhs: frozenset[str]


@dataclass
class PartialFDGroup:
    """Task 6 canonical: one LHS group -> RHS attributes."""

    lhs: frozenset[str]
    rhs: frozenset[str]
