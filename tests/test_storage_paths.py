"""Регрессия: пути загрузок не должны выходить за пределы каталога (как в архивном storage)."""

from pathlib import Path

import pytest

from app.services.file_storage import resolve_path_under_upload_dir


def test_resolve_relative_inside_root(tmp_path: Path) -> None:
    sub = tmp_path / "attempt" / "f.xlsx"
    sub.parent.mkdir(parents=True)
    sub.touch()
    r = resolve_path_under_upload_dir("attempt/f.xlsx", root=tmp_path)
    assert r == sub.resolve()


def test_reject_parent_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="внутри каталога"):
        resolve_path_under_upload_dir("../../../etc/passwd", root=tmp_path)
