"""Run Alembic migrations programmatically at startup.

Handles three cases:
  * alembic-managed DB  -> upgrade to head
  * pre-Alembic DB      -> stamp the baseline, then upgrade (adopts existing schema)
  * fresh DB            -> upgrade to head (creates everything)
"""
from __future__ import annotations

import time
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

from alembic import command
from alembic.config import Config

from ..core.config import get_settings
from ..core.logging import get_logger
from .session import engine, is_sqlite

logger = get_logger(__name__)


def _is_missing_db_error(exc: Exception) -> bool:
    # Postgres: FATAL: database "x" does not exist
    return "does not exist" in str(exc)


def _create_postgres_database(url) -> bool:
    """CREATE DATABASE the target on the server, connecting via a maintenance DB.

    Returns True if the database now exists, False if no maintenance DB was
    reachable (server likely still starting — caller should retry). Raises with a
    clear message if the server is reachable but creation is refused (e.g. the
    user lacks CREATEDB).
    """
    dbname = url.database
    for maint in ("postgres", "template1"):
        admin = create_engine(url.set(database=maint), isolation_level="AUTOCOMMIT")
        try:
            with admin.connect() as conn:
                conn.execute(text(f'CREATE DATABASE "{dbname}"'))
            logger.info("Created missing database %r", dbname)
            return True
        except ProgrammingError as exc:
            if "already exists" in str(exc):  # created concurrently — fine
                return True
            raise RuntimeError(
                f"Database {dbname!r} is missing and could not be created: {exc}. "
                "Create it manually or grant CREATEDB to the DB user."
            ) from exc
        except OperationalError:
            continue  # this maintenance DB isn't reachable; try the next
        finally:
            admin.dispose()
    return False


def ensure_database(retries: int = 10, delay: float = 1.5) -> None:
    """Wait for the DB server and ensure the target database exists.

    SQLite is a no-op (the file is created on connect). For Postgres this waits
    for the server to accept connections and CREATE DATABASE if the target is
    missing (e.g. a fresh Cloud SQL / external Postgres)."""
    raw = get_settings().database_url
    if is_sqlite(raw):
        return
    url = make_url(raw)
    for attempt in range(1, retries + 1):
        try:
            with engine.connect():
                return
        except OperationalError as exc:
            if _is_missing_db_error(exc) and _create_postgres_database(url):
                return
            if attempt == retries:
                raise
            logger.warning(
                "Database not ready (attempt %d/%d): %s",
                attempt, retries, str(exc).splitlines()[0],
            )
            time.sleep(delay)

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_BASELINE = "0001_baseline"


def _alembic_config() -> Config:
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    return cfg


def run_migrations() -> None:
    ensure_database()
    tables = set(inspect(engine).get_table_names())
    cfg = _alembic_config()

    if "alembic_version" in tables:
        logger.info("Applying database migrations (upgrade head).")
        command.upgrade(cfg, "head")
    elif "chapters" in tables:
        # Existing pre-Alembic database: adopt it at the baseline, then apply any
        # migrations added after the baseline.
        logger.info("Existing schema found; stamping baseline then upgrading.")
        command.stamp(cfg, _BASELINE)
        command.upgrade(cfg, "head")
    else:
        logger.info("Fresh database; creating schema (upgrade head).")
        command.upgrade(cfg, "head")
