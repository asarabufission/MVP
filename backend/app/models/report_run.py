import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin


class ReportRun(Base, CreatedAtMixin):
    __tablename__ = "report_runs"

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
    client_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
    )
    report_type: Mapped[str] = mapped_column(String(40), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    s3_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rows_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exceptions_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    included_datasource_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        server_default=text("'{}'::uuid[]"),
    )
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    generated_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
