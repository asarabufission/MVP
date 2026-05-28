"""v7.1 connector flow gap columns for drafts, datasources, job_runs"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasource_drafts",
        sa.Column("display_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "datasource_drafts",
        sa.Column("current_step", sa.SmallInteger(), nullable=False, server_default="1"),
    )
    op.add_column("datasource_drafts", sa.Column("schema_hash", sa.CHAR(64), nullable=True))
    op.add_column("datasource_drafts", sa.Column("sample_s3_path", sa.Text(), nullable=True))
    op.add_column("datasource_drafts", sa.Column("draft_payload", JSONB(), nullable=True))
    op.create_check_constraint(
        "ck_datasource_drafts_current_step",
        "datasource_drafts",
        "current_step BETWEEN 1 AND 4",
    )
    op.create_check_constraint(
        "ck_datasource_drafts_status",
        "datasource_drafts",
        "status IN ('DRAFT','ACTIVATED','ABANDONED')",
    )

    op.add_column("datasources", sa.Column("schema_hash", sa.CHAR(64), nullable=True))
    op.add_column("datasources", sa.Column("config", JSONB(), nullable=True))

    op.add_column(
        "job_runs",
        sa.Column("draft_id", PG_UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_job_runs_draft_id",
        "job_runs",
        "datasource_drafts",
        ["draft_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_job_runs_draft_id", "job_runs", type_="foreignkey")
    op.drop_column("job_runs", "draft_id")

    op.drop_column("datasources", "config")
    op.drop_column("datasources", "schema_hash")

    op.drop_constraint("ck_datasource_drafts_status", "datasource_drafts", type_="check")
    op.drop_constraint("ck_datasource_drafts_current_step", "datasource_drafts", type_="check")
    op.drop_column("datasource_drafts", "draft_payload")
    op.drop_column("datasource_drafts", "sample_s3_path")
    op.drop_column("datasource_drafts", "schema_hash")
    op.drop_column("datasource_drafts", "current_step")
    op.drop_column("datasource_drafts", "display_name")
