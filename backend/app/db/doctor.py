"""Startup database preflight.

Run before launching the app (see start.sh): verify the database is reachable,
bring the schema up to date (create/upgrade via Alembic), and confirm every
expected table exists — failing fast with a clear message and a non-zero exit
code if something is wrong, instead of erroring lazily on the first request.

    python -m app.db.doctor
"""
from __future__ import annotations

import sys

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from .. import models  # noqa: F401  (registers every table on Base.metadata)
from ..core.config import get_settings
from .base import Base
from .migrate import ensure_database, run_migrations
from .session import engine


def _dialect(database_url: str) -> str:
    # Scheme only — never print credentials that may be in the URL.
    return database_url.split("://", 1)[0] or "unknown"


def main() -> int:
    url = get_settings().database_url
    print(f"[db] Using {_dialect(url)} database")

    # 1) Reachable / connected? Waits for a server DB, and CREATE DATABASE if the
    #    target is missing (no-op for SQLite).
    try:
        ensure_database()
        with engine.connect():
            pass
    except SQLAlchemyError as exc:
        print(f"[db] ERROR: database not reachable: {exc}", file=sys.stderr)
        print("[db] Check DATABASE_URL in backend/.env and that the server is running.",
              file=sys.stderr)
        return 1
    except RuntimeError as exc:  # e.g. DB missing and can't be auto-created
        print(f"[db] ERROR: {exc}", file=sys.stderr)
        return 1
    print("[db] Reachable ✓")

    # 2) Ensure the schema exists and is at head (idempotent create/upgrade).
    try:
        run_migrations()
    except Exception as exc:  # noqa: BLE001
        print(f"[db] ERROR: migrations failed: {exc}", file=sys.stderr)
        return 1

    # 3) Verify every expected table is present.
    present = set(inspect(engine).get_table_names())
    required = set(Base.metadata.tables.keys())
    missing = required - present
    if missing:
        print(f"[db] ERROR: tables still missing after migration: {sorted(missing)}",
              file=sys.stderr)
        return 1

    print(f"[db] Schema OK ✓ ({len(required)} tables)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
