from __future__ import annotations

import re
import unicodedata

_ARROW_RE = re.compile(r"\s*(?:->|→|=>|⟶|—>|-->|↦)\s*")
_MULTI_SPACE = re.compile(r"\s+")
_LIST_SPLIT = re.compile(r"[,;]\s*|\s+")


def normalize_text(s: str | None) -> str:
    if s is None:
        return ""
    t = unicodedata.normalize("NFKC", str(s)).strip()
    t = _MULTI_SPACE.sub(" ", t)
    return t


def normalize_attribute_name(s: str | None) -> str:
    t = normalize_text(s)
    t = t.strip(" \t*`\"'")
    return _MULTI_SPACE.sub(" ", t)


def normalize_relation_name(s: str | None) -> str:
    return normalize_attribute_name(s)


def normalize_arrow(s: str | None) -> str:
    if s is None:
        return ""
    t = unicodedata.normalize("NFKC", str(s))
    t = _ARROW_RE.sub(" -> ", t)
    t = _MULTI_SPACE.sub(" ", t.strip())
    return t


def normalize_cell_value(s: str | None) -> str:
    return normalize_text(s)


def normalize_fd_text(s: str | None) -> str:
    """Canonical FD string: spaces, arrow form, strip filler words at line start."""
    if s is None:
        return ""
    t = normalize_arrow(s)
    # Remove common Russian explanatory prefixes (line-level)
    t = re.sub(
        r"^(следовательно|итак|значит|тогда|то есть)[:;\s]*",
        "",
        t,
        flags=re.IGNORECASE,
    )
    return _MULTI_SPACE.sub(" ", t.strip())


def normalize_attribute_list_text(s: str | None) -> list[str]:
    """Split attribute list from 'A, B' or 'A B' style."""
    t = normalize_text(s)
    if not t:
        return []
    parts = re.split(r"[,;]\s*|\s+", t)
    return [normalize_attribute_name(p) for p in parts if normalize_attribute_name(p)]
