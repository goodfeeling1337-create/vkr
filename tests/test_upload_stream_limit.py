from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from app.services.file_storage import read_upload_with_size_limit


@pytest.mark.asyncio
async def test_stream_read_allows_payload_within_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class DummySettings:
        max_upload_size_bytes = 8
        upload_dir = tmp_path

    monkeypatch.setattr("app.services.file_storage.get_settings", lambda: DummySettings())
    upload = UploadFile(file=BytesIO(b"12345678"), filename="ok.xlsx")

    data = await read_upload_with_size_limit(upload, label="файл", chunk_size=3)

    assert data == b"12345678"


@pytest.mark.asyncio
async def test_stream_read_rejects_payload_above_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class DummySettings:
        max_upload_size_bytes = 8
        upload_dir = tmp_path

    monkeypatch.setattr("app.services.file_storage.get_settings", lambda: DummySettings())
    upload = UploadFile(file=BytesIO(b"123456789"), filename="too-big.xlsx")

    with pytest.raises(ValueError, match="превышает допустимый лимит"):
        await read_upload_with_size_limit(upload, label="файл", chunk_size=4)
