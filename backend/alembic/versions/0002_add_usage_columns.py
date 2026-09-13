"""Ensure token/cost usage columns exist on chapters and assessments.

The 0001 baseline uses ``create_all``, so a *pre-Alembic* database is stamped at
baseline as if it already had every current column. A database created before
the usage-tracking columns were introduced therefore never received them, and
inserts fail with "table chapters has no column named tokens_input". This
migration adds any of those columns that are missing (idempotent), so both such
legacy databases and fresh ones converge on the right schema.

Revision ID: 0002_add_usage_columns
Revises: 0001_baseline
Create Date: 2026-09-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = "0002_add_usage_columns"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (column, type, server_default) for the usage columns, added to each table.
_COLUMNS = (
    ("tokens_input", sa.Integer(), "0"),
    ("tokens_output", sa.Integer(), "0"),
    ("cost_usd", sa.Float(), "0.0"),
)
_TABLES = ("chapters", "assessments")


def _existing_columns(inspector, table: str) -> set[str]:
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    for table in _TABLES:
        present = _existing_columns(inspector, table)
        if not present:
            continue  # table doesn't exist yet (shouldn't happen post-baseline)
        missing = [(name, type_, default) for name, type_, default in _COLUMNS
                   if name not in present]
        if not missing:
            continue
        with op.batch_alter_table(table) as batch:
            for name, type_, default in missing:
                batch.add_column(
                    sa.Column(name, type_, nullable=False, server_default=default)
                )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    for table in _TABLES:
        present = _existing_columns(inspector, table)
        drop = [name for name, _type, _default in _COLUMNS if name in present]
        if not drop:
            continue
        with op.batch_alter_table(table) as batch:
            for name in drop:
                batch.drop_column(name)
