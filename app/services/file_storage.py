from __future__ import annotations

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


def store_upload(data: bytes, prefix: str, original_name: str) -> Path:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix or ".bin"
    name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = settings.upload_dir / name
    path.write_bytes(data)
    return path
