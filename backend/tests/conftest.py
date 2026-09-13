"""Shared pytest fixtures.

The database is pointed at a temporary SQLite file and OpenAI is never called —
tests either exercise pure logic or stub the ``LLMClient``.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

# Isolate the DB and force a fake key BEFORE app modules import settings.
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_study_notes.db")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    # Start every run from a clean database so file-backed SQLite state can't
    # accumulate across pytest invocations (which would break aggregation tests).
    db_url = os.environ["DATABASE_URL"]
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "", 1)
        for suffix in ("", "-wal", "-shm", "-journal"):
            try:
                os.remove(db_path + suffix)
            except FileNotFoundError:
                pass

    from app.db.session import init_db

    init_db()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_chapter():
    """A lightweight stand-in for the Chapter ORM object."""
    return SimpleNamespace(
        id=1,
        chapter_name="Photosynthesis",
        class_name="Class 10",
        subject="Biology",
        notes="## Overview\nSome **notes**.\n\n- a\n- b",
        raw_text="raw text",
    )
