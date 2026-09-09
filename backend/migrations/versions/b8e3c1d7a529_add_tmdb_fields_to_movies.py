"""Add TMDB fields to movies

Revision ID: b8e3c1d7a529
Revises: 04aa56a89241
Create Date: 2026-06-25 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8e3c1d7a529"
down_revision: str | Sequence[str] | None = "04aa56a89241"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("movies", sa.Column("tmdb_id", sa.Integer(), nullable=True))
    op.add_column("movies", sa.Column("tmdb_title", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("poster_path", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("overview", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("runtime", sa.Integer(), nullable=True))
    op.add_column("movies", sa.Column("certification", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("release_date", sa.String(), nullable=True))
    op.create_index("ix_movies_tmdb_id", "movies", ["tmdb_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_movies_tmdb_id", table_name="movies")
    op.drop_column("movies", "release_date")
    op.drop_column("movies", "certification")
    op.drop_column("movies", "runtime")
    op.drop_column("movies", "overview")
    op.drop_column("movies", "poster_path")
    op.drop_column("movies", "tmdb_title")
    op.drop_column("movies", "tmdb_id")
