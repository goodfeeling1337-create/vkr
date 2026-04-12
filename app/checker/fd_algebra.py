from __future__ import annotations

import re
from collections import defaultdict

from app.checker.normalizers import normalize_attribute_name
from app.domain.fd import FunctionalDependency, FunctionalDependencySet

def split_elementary_from_line(line: str) -> list[FunctionalDependency]:
    from app.checker.normalizers import normalize_fd_text

    t = normalize_fd_text(line)
    if "->" not in t:
        return []
    lhs_raw, rhs_raw = t.split("->", 1)
    lhs_raw = lhs_raw.strip()
    rhs_raw = rhs_raw.strip()
    if not lhs_raw or not rhs_raw:
        return []
    lhs_attrs = _parse_attr_set(lhs_raw)
    rhs_attrs = _parse_attr_list(rhs_raw)
    out: list[FunctionalDependency] = []
    for r in rhs_attrs:
        out.append(FunctionalDependency(frozenset(lhs_attrs), r))
    return out


def _parse_attr_set(s: str) -> set[str]:
    s = s.strip().strip("{}[]()")
    parts = re.split(r"[,;\s]+", s)
    return {normalize_attribute_name(p) for p in parts if normalize_attribute_name(p)}


def _parse_attr_list(s: str) -> list[str]:
    parts = re.split(r"[,;\s]+", s)
    return [normalize_attribute_name(p) for p in parts if normalize_attribute_name(p)]


def elementary_fd_set(lines: list[str]) -> FunctionalDependencySet:
    fs = FunctionalDependencySet()
    for ln in lines:
        for fd in split_elementary_from_line(ln):
            fs.add(fd)
    return fs


def group_by_lhs(lines: list[str]) -> dict[frozenset[str], set[str]]:
    """Merge elementary RHS per LHS group for comparison."""
    g: dict[frozenset[str], set[str]] = defaultdict(set)
    for ln in lines:
        for fd in split_elementary_from_line(ln):
            g[fd.lhs].add(fd.rhs)
    return {k: set(v) for k, v in g.items()}
