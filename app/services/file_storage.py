from __future__ import annotations

import os
import uuid
from pathlib import Path

from app.core.config import get_settings


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
    """Legacy helper: writes file directly to final path."""
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix or ".bin"
    name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = settings.upload_dir / name
    path.write_bytes(data)
    return path


def store_upload_temp(data: bytes, prefix: str, original_name: str) -> tuple[Path, Path]:
    """
    Writes to a temp path first and returns (temp_path, final_path).
    Caller must finalize or discard temp file.
    """
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix or ".bin"
    name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    final_path = settings.upload_dir / name
    temp_path = settings.upload_dir / f"{name}.tmp"
    temp_path.write_bytes(data)
    return temp_path, final_path


def finalize_upload_temp(temp_path: Path, final_path: Path) -> Path:
    """Atomically moves temp file to final destination."""
    os.replace(temp_path, final_path)
    return final_path


def discard_upload_temp(temp_path: Path) -> None:
    """Best-effort temp cleanup."""
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        pass
