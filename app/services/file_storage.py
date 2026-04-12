from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import get_settings


def store_upload(data: bytes, prefix: str, original_name: str) -> Path:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix or ".bin"
    name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = settings.upload_dir / name
    path.write_bytes(data)
    return path
