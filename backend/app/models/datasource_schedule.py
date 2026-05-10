import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DatasourceSchedule(Base, TimestampMixin):
    __tablename__ = "datasource_schedules"
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('MANUAL','DAILY','WEEKLY','MONTHLY')",
            name="ck_datasource_schedules_frequency",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    datasource_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("datasources.id"),
        nullable=False,
        unique=True,
    )
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    time_of_day: Mapped[str | None] = mapped_column(String(5), nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        server_default=text("'America/New_York'"),
    )
    cron_expression: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )
