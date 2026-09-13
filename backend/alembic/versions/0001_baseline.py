"""Baseline schema (chapters, questions, generation_jobs, assessments).

This captures the full schema as of the switch to Alembic. Pre-existing
databases are stamped at this revision instead of re-running it; future changes
get their own incremental migrations.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op

from app.db.base import Base
import app.models  # noqa: F401  (register all tables on Base.metadata)

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
