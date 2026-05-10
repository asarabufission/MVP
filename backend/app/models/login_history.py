import uuid
from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LoginHistory(Base, TimestampMixin):
    __tablename__ = "login_history"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE','LOGGED_OUT','EXPIRED','REVOKED')",
            name="ck_login_history_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    msp_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("msps.id"),
        nullable=False,
    )
    access_token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
