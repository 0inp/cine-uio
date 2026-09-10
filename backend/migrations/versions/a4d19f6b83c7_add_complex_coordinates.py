"""Add coordinates to cinema complexes

Revision ID: a4d19f6b83c7
Revises: f2c8a05e91db
Create Date: 2026-09-10 17:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4d19f6b83c7"
down_revision: str | Sequence[str] | None = "f2c8a05e91db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Left empty here on purpose: the values come from the chains, so re-running
    # app.seed fills them rather than freezing a copy inside a migration.
    op.add_column("cinema_complexes", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("cinema_complexes", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("cinema_complexes", "longitude")
    op.drop_column("cinema_complexes", "latitude")
