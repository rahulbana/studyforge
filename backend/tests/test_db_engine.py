"""Per-dialect engine options for the switchable SQLite/Postgres DATABASE_URL."""
from sqlalchemy import create_engine

from app.db.session import engine_kwargs, is_sqlite


def test_sqlite_gets_check_same_thread():
    kw = engine_kwargs("sqlite:///./data/x.db")
    assert kw == {"connect_args": {"check_same_thread": False}}
    assert is_sqlite("sqlite:///x.db") is True


def test_postgres_gets_pool_pre_ping_no_connect_args():
    kw = engine_kwargs("postgresql+psycopg://u:p@host:5432/db")
    assert kw == {"pool_pre_ping": True}
    assert is_sqlite("postgresql+psycopg://u:p@host/db") is False


def test_engine_builds_for_postgres_url():
    # create_engine is lazy (no connection opened), so this validates the driver
    # is importable and the URL/options are accepted.
    eng = create_engine(
        "postgresql+psycopg://u:p@localhost:5432/db", **engine_kwargs("postgresql+psycopg://x")
    )
    assert eng.dialect.name == "postgresql"
    eng.dispose()
