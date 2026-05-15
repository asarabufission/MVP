import uuid
from datetime import datetime

from app.schemas.common import CamelModel


class DatasourceListItem(CamelModel):
    id: uuid.UUID
    name: str
    vendor: str
    category: str
    source_type: str
    scope: str
    status: str
    last_run_at: datetime | None = None
    created_at: datetime
    client_id: uuid.UUID | None = None
    blueprint_id: str | None = None


class DatasourceListResponse(CamelModel):
    items: list[DatasourceListItem]
    total_count: int
