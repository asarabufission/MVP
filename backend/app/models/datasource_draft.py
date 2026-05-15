import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
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
