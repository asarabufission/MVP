import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("msp_id", "name", name="uq_clients_msp_name"),)

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
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_identifier_type: Mapped[str] = mapped_column(String(60), nullable=False)
    default_identifier_value: Mapped[str] = mapped_column(String(160), nullable=False)
    readiness: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'NEEDS_SETUP'"),
    )
