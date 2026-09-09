"""Add city to cinema complexes and guard complex names within a chain

Revision ID: d7a4c2f81b60
Revises: c4f2a91b6d38
Create Date: 2026-09-09 13:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7a4c2f81b60"
down_revision: str | Sequence[str] | None = "c4f2a91b6d38"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cinema_complexes", sa.Column("city", sa.String(), nullable=False, server_default=""))
    op.create_index("ix_cinema_complexes_city", "cinema_complexes", ["city"])
    # Every complex that existed before this migration was in Quito.
    op.execute("UPDATE cinema_complexes SET city = 'Quito' WHERE city = ''")
    with op.batch_alter_table("cinema_complexes") as batch:
        batch.create_unique_constraint("uq_complex_company_name", ["company_id", "name"])


def downgrade() -> None:
    with op.batch_alter_table("cinema_complexes") as batch:
        batch.drop_constraint("uq_complex_company_name", type_="unique")
    op.drop_index("ix_cinema_complexes_city", table_name="cinema_complexes")
    op.drop_column("cinema_complexes", "city")
