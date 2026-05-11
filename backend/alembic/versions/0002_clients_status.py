"""add clients.status soft-delete column"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
    )
    op.create_check_constraint(
        "ck_clients_status",
        "clients",
        "status IN ('ACTIVE','INACTIVE')",
    )
    op.create_index(
        "ix_clients_msp_status_created",
        "clients",
        ["msp_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_clients_msp_status_created", table_name="clients")
    op.drop_constraint("ck_clients_status", "clients", type_="check")
    op.drop_column("clients", "status")
