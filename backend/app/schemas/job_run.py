import uuid
from datetime import datetime

from app.schemas.common import CamelModel


class JobRunListItem(CamelModel):
    id: uuid.UUID
    status: str
    datasource_name: str | None = None
    client_name: str | None = None
    job_type: str
    started_at: datetime
    ended_at: datetime | None = None
    records: int | None = None
    error_message: str | None = None
