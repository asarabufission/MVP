import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Datasource(Base, TimestampMixin):
    __tablename__ = "datasources"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE','ACTIVATING','DRAFT','DEGRADED','DISABLED','INACTIVE')",
            name="ck_datasources_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    msp_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("msps.id"),
        nullable=False,
    )
    draft_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasource_drafts.id"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    vendor: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scope: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    active_mapping_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    secret_arn: Mapped[str] = mapped_column(String(400), nullable=False)
    glue_table_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    landing_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    inactivated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
