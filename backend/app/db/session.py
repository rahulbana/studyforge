"""Database engine, session factory, and lifecycle helpers."""
from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import get_settings
from .base import Base  # noqa: F401  (kept for callers importing Base from here)

settings = get_settings()


def is_sqlite(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def _ensure_sqlite_dir(database_url: str) -> None:
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)


def engine_kwargs(database_url: str) -> dict:
    """Per-dialect create_engine options.

    SQLite needs check_same_thread=False (it's used across the request thread and
    background threads). Server databases (Postgres) get pool_pre_ping so stale
    pooled connections are recycled instead of erroring after an idle period or a
    DB restart.
    """
    if is_sqlite(database_url):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


_ensure_sqlite_dir(settings.database_url)

engine = create_engine(settings.database_url, **engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Bring the database schema up to date via Alembic migrations."""
    from .migrate import run_migrations

    run_migrations()
