"""Replace format/language with projection/audio

Revision ID: f2c8a05e91db
Revises: e91f3b7c2a04
Create Date: 2026-09-10 16:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2c8a05e91db"
down_revision: str | Sequence[str] | None = "e91f3b7c2a04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The backfill is expressed in SQL rather than by importing app.screening_types:
# a migration has to keep producing the same result years from now, whatever that
# module has become since.
_BACKFILL_PROJECTION = """
UPDATE screenings SET projection = CASE
    WHEN language LIKE '%4D%' OR format LIKE '%4D%' THEN '4D'
    WHEN language LIKE '%3D%' OR format LIKE '%3D%' THEN '3D'
    ELSE '2D'
END
"""

# Subtitled is tested first: "Subtitulada en español" is not a dubbed showing.
_BACKFILL_AUDIO = """
UPDATE screenings SET audio = CASE
    WHEN lower(language) LIKE '%sub%' THEN 'subtitled'
    WHEN lower(language) LIKE '%esp%' OR lower(language) LIKE '%dobl%' THEN 'dubbed'
    ELSE NULL
END
"""


def upgrade() -> None:
    op.add_column("screenings", sa.Column("projection", sa.String(), nullable=False, server_default="2D"))
    op.add_column("screenings", sa.Column("audio", sa.String(), nullable=True))
    op.execute(_BACKFILL_PROJECTION)
    op.execute(_BACKFILL_AUDIO)
    with op.batch_alter_table("screenings") as batch:
        batch.drop_column("format")
        batch.drop_column("language")


def downgrade() -> None:
    op.add_column("screenings", sa.Column("format", sa.String(), nullable=False, server_default=""))
    op.add_column("screenings", sa.Column("language", sa.String(), nullable=False, server_default=""))
    # The room type is not recoverable — it was deliberately dropped, not moved.
    op.execute("UPDATE screenings SET format = projection")
    op.execute(
        "UPDATE screenings SET language = CASE audio "
        "WHEN 'dubbed' THEN 'Doblada' WHEN 'subtitled' THEN 'Subtitulada' ELSE '' END"
    )
    with op.batch_alter_table("screenings") as batch:
        batch.drop_column("audio")
        batch.drop_column("projection")
