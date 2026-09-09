"""Add scrape_runs

Revision ID: e91f3b7c2a04
Revises: d7a4c2f81b60
Create Date: 2026-09-09 17:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e91f3b7c2a04"
down_revision: str | Sequence[str] | None = "d7a4c2f81b60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("complexes_succeeded", sa.Integer(), nullable=False),
        sa.Column("complexes_failed", sa.Integer(), nullable=False),
        sa.Column("failures", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_runs_started_at", "scrape_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_scrape_runs_started_at", table_name="scrape_runs")
    op.drop_table("scrape_runs")
