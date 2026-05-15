"""add v7.1 client_id + blueprint_id columns to drafts and datasources"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasource_drafts",
        sa.Column("client_id", PG_UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_datasource_drafts_client_id",
        "datasource_drafts",
        "clients",
        ["client_id"],
        ["id"],
    )
    op.add_column(
        "datasource_drafts",
        sa.Column("blueprint_id", sa.String(80), nullable=True),
    )

    op.add_column(
        "datasources",
        sa.Column("client_id", PG_UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_datasources_client_id",
        "datasources",
        "clients",
        ["client_id"],
        ["id"],
    )
    op.add_column(
        "datasources",
        sa.Column("blueprint_id", sa.String(80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("datasources", "blueprint_id")
    op.drop_constraint("fk_datasources_client_id", "datasources", type_="foreignkey")
    op.drop_column("datasources", "client_id")

    op.drop_column("datasource_drafts", "blueprint_id")
    op.drop_constraint(
        "fk_datasource_drafts_client_id", "datasource_drafts", type_="foreignkey"
    )
    op.drop_column("datasource_drafts", "client_id")
