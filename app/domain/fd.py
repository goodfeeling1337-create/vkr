from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FunctionalDependency:
    lhs: frozenset[str]
    rhs: str

    def as_tuple(self) -> tuple[tuple[str, ...], str]:
        return (tuple(sorted(self.lhs)), self.rhs)


@dataclass
class FunctionalDependencySet:
    fds: set[FunctionalDependency] = field(default_factory=set)

    def add(self, fd: FunctionalDependency) -> None:
        self.fds.add(fd)
