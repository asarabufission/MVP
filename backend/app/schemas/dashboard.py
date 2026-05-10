import uuid
from datetime import datetime

from app.schemas.common import CamelModel


class FailedRunItem(CamelModel):
    id: uuid.UUID
    datasource_name: str | None = None
    error: str | None = None
    started_at: datetime


class RecentActivityItem(CamelModel):
    id: uuid.UUID
    status: str
    datasource_name: str | None = None
    client_name: str | None = None
    type: str
    started_at: datetime
    ended_at: datetime | None = None
    records: int | None = None


class DashboardSummary(CamelModel):
    clients_ready: int
    total_clients: int
    active_datasources: int
    total_datasources: int
    recent_runs_count: int
    reports_generated: int
    failed_runs: list[FailedRunItem]
    recent_activity: list[RecentActivityItem]
