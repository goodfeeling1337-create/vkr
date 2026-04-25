"""Регрессия: пути загрузок не должны выходить за пределы каталога (как в архивном storage)."""

from pathlib import Path

import pytest

from app.services.file_storage import (
    discard_upload_temp,
    finalize_upload_temp,
    resolve_path_under_upload_dir,
    store_upload_temp,
)


def test_resolve_relative_inside_root(tmp_path: Path) -> None:
    sub = tmp_path / "attempt" / "f.xlsx"
    sub.parent.mkdir(parents=True)
    sub.touch()
    r = resolve_path_under_upload_dir("attempt/f.xlsx", root=tmp_path)
    assert r == sub.resolve()


def test_reject_parent_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="внутри каталога"):
        resolve_path_under_upload_dir("../../../etc/passwd", root=tmp_path)


def test_finalize_temp_upload_writes_final_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class DummySettings:
        upload_dir = tmp_path

    monkeypatch.setattr("app.services.file_storage.get_settings", lambda: DummySettings())
    temp_path, final_path = store_upload_temp(b"abc", "attempt", "x.xlsx")
    assert temp_path.exists()
    assert not final_path.exists()

    finalize_upload_temp(temp_path, final_path)

    assert not temp_path.exists()
    assert final_path.exists()
    assert final_path.read_bytes() == b"abc"


def test_discard_temp_upload_removes_temp_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class DummySettings:
        upload_dir = tmp_path

    monkeypatch.setattr("app.services.file_storage.get_settings", lambda: DummySettings())
    temp_path, _ = store_upload_temp(b"abc", "review", "r.xlsx")
    assert temp_path.exists()

    discard_upload_temp(temp_path)

    assert not temp_path.exists()
