import uuid
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DatasourceDraft(Base, TimestampMixin):
    __tablename__ = "datasource_drafts"
    __table_args__ = (
        CheckConstraint(
            "category IN ('LICENSING','ENDPOINT','RECONCILIATION')",
            name="ck_datasource_drafts_category",
        ),
        CheckConstraint(
            "source_type IN ('API','FILE_UPLOAD')",
            name="ck_datasource_drafts_source_type",
        ),
        CheckConstraint(
            "scope IN ('MSP_LEVEL','CLIENT_SPECIFIC')",
            name="ck_datasource_drafts_scope",
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
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    vendor: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scope: Mapped[str] = mapped_column(String(40), nullable=False)
    secret_arn: Mapped[str | None] = mapped_column(String(400), nullable=True)
    last_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default=text("'DRAFT'"),
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=True,
    )
    blueprint_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_step: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=text("1"),
    )
    schema_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sample_s3_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
