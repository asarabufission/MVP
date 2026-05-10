"""initial schema — 10 tables, indexes, partial unique indexes"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "msps",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(160), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column("username", sa.String(120), nullable=False, unique=True),
        sa.Column("email", sa.String(120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=True),
        sa.Column(
            "role",
            sa.String(40),
            nullable=False,
            server_default=sa.text("'MSP_ADMIN'"),
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "role IN ('MSP_ADMIN','MSP_ANALYST')",
            name="ck_users_role",
        ),
    )

    op.create_table(
        "login_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column("access_token_hash", sa.CHAR(64), nullable=False),
        sa.Column("refresh_token_hash", sa.CHAR(64), nullable=False),
        sa.Column("login_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("logout_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('ACTIVE','LOGGED_OUT','EXPIRED','REVOKED')",
            name="ck_login_history_status",
        ),
    )

    op.create_table(
        "clients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("default_identifier_type", sa.String(60), nullable=False),
        sa.Column("default_identifier_value", sa.String(160), nullable=False),
        sa.Column(
            "readiness",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'NEEDS_SETUP'"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("msp_id", "name", name="uq_clients_msp_name"),
    )

    op.create_table(
        "datasource_drafts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("vendor", sa.String(160), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("scope", sa.String(40), nullable=False),
        sa.Column("secret_arn", sa.String(400), nullable=True),
        sa.Column("last_attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(40),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "category IN ('LICENSING','ENDPOINT','RECONCILIATION')",
            name="ck_datasource_drafts_category",
        ),
        sa.CheckConstraint(
            "source_type IN ('API','FILE_UPLOAD')",
            name="ck_datasource_drafts_source_type",
        ),
        sa.CheckConstraint(
            "scope IN ('MSP_LEVEL','CLIENT_SPECIFIC')",
            name="ck_datasource_drafts_scope",
        ),
    )

    op.create_table(
        "datasources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column(
            "draft_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasource_drafts.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("vendor", sa.String(160), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("scope", sa.String(40), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column(
            "active_mapping_version",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("secret_arn", sa.String(400), nullable=False),
        sa.Column("glue_table_name", sa.String(200), nullable=True),
        sa.Column("landing_path", sa.String(500), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "inactivated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('ACTIVE','ACTIVATING','DRAFT','DEGRADED','DISABLED','INACTIVE')",
            name="ck_datasources_status",
        ),
    )

    op.create_table(
        "datasource_schedules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "datasource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasources.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("time_of_day", sa.String(5), nullable=True),
        sa.Column(
            "timezone",
            sa.String(60),
            nullable=False,
            server_default=sa.text("'America/New_York'"),
        ),
        sa.Column("cron_expression", sa.String(120), nullable=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "frequency IN ('MANUAL','DAILY','WEEKLY','MONTHLY')",
            name="ck_datasource_schedules_frequency",
        ),
    )

    op.create_table(
        "client_datasource_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "datasource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "is_billing_source",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "is_identity_anchor",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column("identifier_type", sa.String(60), nullable=True),
        sa.Column("identifier_value", sa.String(160), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("inactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "inactivated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "assigned_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("client_id", "datasource_id", name="uq_cda_client_datasource"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_cda_status"),
    )

    op.create_table(
        "job_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column(
            "datasource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasources.id"),
            nullable=True,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=True,
        ),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_count", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("landing_s3_path", sa.String(500), nullable=True),
        sa.Column("glue_table_name", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "report_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "msp_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("msps.id"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("report_type", sa.String(40), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("s3_uri", sa.String(500), nullable=True),
        sa.Column("rows_count", sa.Integer, nullable=True),
        sa.Column("exceptions_count", sa.Integer, nullable=True),
        sa.Column(
            "included_datasource_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("'{}'::uuid[]"),
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "generated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_login_history_user_status", "login_history", ["user_id", "status"])
    op.create_index("ix_datasources_msp_status", "datasources", ["msp_id", "status"])
    op.execute(
        "CREATE INDEX ix_job_runs_msp_started_desc "
        "ON job_runs (msp_id, started_at DESC)"
    )
    op.create_index(
        "ix_cda_client_status",
        "client_datasource_assignments",
        ["client_id", "status"],
    )
    op.create_index(
        "ix_cda_datasource_status",
        "client_datasource_assignments",
        ["datasource_id", "status"],
    )

    op.create_index(
        "ux_client_billing_source",
        "client_datasource_assignments",
        ["client_id"],
        unique=True,
        postgresql_where=sa.text("is_billing_source = TRUE AND status = 'ACTIVE'"),
    )
    op.create_index(
        "ux_client_identity_anchor",
        "client_datasource_assignments",
        ["client_id"],
        unique=True,
        postgresql_where=sa.text("is_identity_anchor = TRUE AND status = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index("ux_client_identity_anchor", table_name="client_datasource_assignments")
    op.drop_index("ux_client_billing_source", table_name="client_datasource_assignments")
    op.drop_index("ix_cda_datasource_status", table_name="client_datasource_assignments")
    op.drop_index("ix_cda_client_status", table_name="client_datasource_assignments")
    op.execute("DROP INDEX IF EXISTS ix_job_runs_msp_started_desc")
    op.drop_index("ix_datasources_msp_status", table_name="datasources")
    op.drop_index("ix_login_history_user_status", table_name="login_history")

    op.drop_table("report_runs")
    op.drop_table("job_runs")
    op.drop_table("client_datasource_assignments")
    op.drop_table("datasource_schedules")
    op.drop_table("datasources")
    op.drop_table("datasource_drafts")
    op.drop_table("clients")
    op.drop_table("login_history")
    op.drop_table("users")
    op.drop_table("msps")

    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
