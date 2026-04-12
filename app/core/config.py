from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    secret_key: str = "dev-secret-change-me"
    database_url: str = "postgresql+psycopg://dn_user:dn_pass@localhost:5432/dn_db"
    upload_dir: Path = Path("./uploads")
    session_cookie_name: str = "dn_session"
    session_max_age: int = 86400 * 7
    log_level: str = "INFO"
    default_scoring_mode: Literal["training", "testing"] = "training"
    allow_optional_pure_junction_relations: bool = True

    @property
    def sync_database_url(self) -> str:
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
