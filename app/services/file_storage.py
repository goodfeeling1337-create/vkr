from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from fastapi import UploadFile


def resolve_path_under_upload_dir(path: str | Path, *, root: Path | None = None) -> Path:
    """
    Проверяет, что путь указывает внутрь каталога загрузок (защита от обхода каталога).
    Как в архивном storage.resolve_path: абсолютные пути вне root отклоняются.
    """
    base = (root or get_settings().upload_dir).resolve()
    raw = Path(path).expanduser()
    resolved = raw.resolve() if raw.is_absolute() else (base / raw).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError("Доступ к файлу запрещён: путь должен находиться внутри каталога загрузок.") from exc
    return resolved


def validate_upload_size(data: bytes, *, label: str = "файл") -> None:
    """Бросает ValueError если файл превышает лимит."""
    limit = get_settings().max_upload_size_bytes
    if len(data) > limit:
        mb = limit // (1024 * 1024)
        raise ValueError(
            f"Размер файла превышает допустимый лимит ({mb} МБ). "
            "Загрузите файл меньшего размера."
        )


def store_upload(data: bytes, prefix: str, original_name: str) -> Path:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix or ".bin"
    name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = settings.upload_dir / name
    path.write_bytes(data)
    return path


async def read_upload_with_size_limit(
    upload: "UploadFile",
    *,
    label: str = "файл",
    chunk_size: int = 1024 * 1024,
) -> bytes:
    """
    Reads UploadFile in chunks and stops as soon as size limit is exceeded.
    """
    limit = get_settings().max_upload_size_bytes
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            mb = limit // (1024 * 1024)
            raise ValueError(
                f"Размер {label} превышает допустимый лимит ({mb} МБ). "
                "Загрузите файл меньшего размера."
            )
        chunks.append(chunk)
    return b"".join(chunks)
