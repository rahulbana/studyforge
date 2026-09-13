"""Regression: a pre-Alembic DB missing the usage columns is healed on upgrade.

Reproduces "table chapters has no column named tokens_input": a database created
before the token/cost columns existed, stamped at baseline, must gain those
columns when migrations run to head (via 0002).
"""
from __future__ import annotations

import os
from pathlib import Path

import sqlalchemy as sa

from alembic import command
from alembic.config import Config
from app.core.config import get_settings

_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _legacy_config(db_path: Path) -> Config:
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url  # env.py reads this via get_settings()
    get_settings.cache_clear()
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    return cfg, url


def test_upgrade_adds_missing_usage_columns(tmp_path, monkeypatch):
    original_url = os.environ.get("DATABASE_URL")
    db_path = tmp_path / "legacy.db"

    # A legacy chapters table WITHOUT tokens_input/tokens_output/cost_usd, and no
    # alembic_version — exactly the shape that used to break inserts.
    legacy = sa.create_engine(f"sqlite:///{db_path}")
    with legacy.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE chapters (id INTEGER PRIMARY KEY, class_name TEXT, "
            "subject TEXT, chapter_name TEXT, source_filename TEXT, raw_text TEXT, "
            "notes TEXT, sources TEXT, notes_status TEXT, notes_error TEXT, "
            "created_at TEXT)"
        ))
    legacy.dispose()

    try:
        cfg, url = _legacy_config(db_path)
        # Mimic the bootstrap for a pre-Alembic DB: stamp baseline, then upgrade.
        command.stamp(cfg, "0001_baseline")
        command.upgrade(cfg, "head")

        eng = sa.create_engine(url)
        cols = {c["name"] for c in sa.inspect(eng).get_columns("chapters")}
        assert {"tokens_input", "tokens_output", "cost_usd"} <= cols

        # And an insert with the usage columns now succeeds.
        with eng.begin() as conn:
            conn.execute(sa.text(
                "INSERT INTO chapters (class_name, subject, chapter_name, "
                "notes_status, tokens_input, tokens_output, cost_usd) "
                "VALUES ('9', 'Sci', 'Ch', 'pending', 0, 0, 0.0)"
            ))
        eng.dispose()
    finally:
        if original_url is not None:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)
        get_settings.cache_clear()
