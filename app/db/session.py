from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Ленивая инициализация движка (позволяет сменить DATABASE_URL до первого подключения)."""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine(
            get_settings().sync_database_url,
            echo=False,
            pool_pre_ping=True,
        )
        _session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            class_=Session,
        )
    return _engine


def reset_engine() -> None:
    """Сброс движка и фабрики сессий (тесты или смена DATABASE_URL)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
    get_settings.cache_clear()


def SessionLocal() -> Session:
    """Создаёт новую синхронную сессию БД (совместимо с прежним sessionmaker()())."""
    get_engine()
    assert _session_factory is not None
    return _session_factory()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
