from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # development | production — влияет на безопасные значения по умолчанию для cookie
    app_environment: Literal["development", "production"] = "development"
    secret_key: str = "dev-secret-change-me"
    database_url: str = "postgresql+psycopg://dn_user:dn_pass@localhost:5432/dn_db"
    upload_dir: Path = Path("./uploads")
    session_cookie_name: str = "dn_session"
    session_max_age: int = 86400 * 7
    # В production задайте SESSION_COOKIE_SECURE=true за HTTPS
    session_cookie_secure: bool = False
    log_level: str = "INFO"
    default_scoring_mode: Literal["training", "testing"] = "training"
    allow_optional_pure_junction_relations: bool = True

    @property
    def sync_database_url(self) -> str:
        return self.database_url

    @model_validator(mode="after")
    def _production_must_be_safe(self) -> Settings:
        if self.app_environment != "production":
            return self
        weak = {"dev-secret-change-me", "change-me-in-production", ""}
        if self.secret_key in weak or len(self.secret_key) < 16:
            raise ValueError(
                "Для APP_ENVIRONMENT=production задайте SECRET_KEY длиной не менее 16 символов "
                "(не используйте значения по умолчанию из .env.example)."
            )
        if not self.session_cookie_secure:
            raise ValueError(
                "Для production задайте SESSION_COOKIE_SECURE=true (сессионная cookie только по HTTPS)."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
