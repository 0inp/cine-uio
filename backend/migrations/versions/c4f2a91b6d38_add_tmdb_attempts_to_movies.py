"""Add tmdb_attempts to movies

Revision ID: c4f2a91b6d38
Revises: b8e3c1d7a529
Create Date: 2026-09-08 23:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4f2a91b6d38"
down_revision: str | Sequence[str] | None = "b8e3c1d7a529"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "movies",
        sa.Column("tmdb_attempts", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("movies", "tmdb_attempts")
