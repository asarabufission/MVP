import uuid
from datetime import datetime
from typing import Any, Literal

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
    updated_at: datetime | None = None
    inactivated_at: datetime | None = None
    client_id: uuid.UUID | None = None
    blueprint_id: str | None = None


class DatasourceListResponse(CamelModel):
    items: list[DatasourceListItem]
    total_count: int


class DatasourceScheduleResponse(CamelModel):
    frequency: str
    time_of_day: str | None = None
    timezone: str
    is_enabled: bool


class DatasourceDetailResponse(CamelModel):
    id: uuid.UUID
    name: str
    vendor: str
    category: str
    source_type: str
    scope: str
    status: str
    blueprint_id: str | None = None
    client_id: uuid.UUID | None = None
    client_name: str | None = None
    config: dict[str, Any] | None = None
    schema_hash: str | None = None
    landing_path: str | None = None
    glue_table_name: str | None = None
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    inactivated_at: datetime | None = None
    schedule: DatasourceScheduleResponse | None = None


class DatasourceDeleteResponse(CamelModel):
    id: uuid.UUID
    status: str
    inactivated_at: datetime | None = None
    message: str = "Datasource soft-deleted (status set to INACTIVE)"


class DatasourcePatchRequest(CamelModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    schedule: DatasourceScheduleResponse | None = None


class DraftCreateRequest(CamelModel):
    client_id: uuid.UUID
    blueprint_id: str
    name: str | None = None
    display_name: str | None = None
    config: dict[str, Any] | None = None


class DraftCreateResponse(CamelModel):
    draft_id: uuid.UUID
    status: str
    current_step: int
    blueprint_details: dict[str, Any]


class TestConnectionRequest(CamelModel):
    credentials: dict[str, Any]
    attempt_id: uuid.UUID


class SchemaFieldPreview(CamelModel):
    name: str
    type: str
    nullable: bool = True
    sample_values: list[Any] | None = None


class TestConnectionResponse(CamelModel):
    test_run_id: uuid.UUID
    schema_hash: str
    fields: list[SchemaFieldPreview]
    sample_rows: list[dict[str, Any]]
    record_count: int
    column_count: int
    connection_time_ms: int
    sample_s3_path: str
    cached: bool = False


class SchemaPreviewResponse(CamelModel):
    fields: list[SchemaFieldPreview]
    schema_hash: str
    sample_rows: list[dict[str, Any]]
    record_count: int
    column_count: int
    expires_at: str | None = None
    standard_fields: list[dict[str, Any]]


class FieldMappingItem(CamelModel):
    standard_field: str
    source_field: str
    transform: str = "none"


class ActivateMapping(CamelModel):
    standard_schema: str | None = None
    schema_hash: str
    field_mappings: list[FieldMappingItem]
    additional_params: list[dict[str, str]] | None = None


class ActivateSchedule(CamelModel):
    frequency: Literal["MANUAL", "DAILY", "WEEKLY", "MONTHLY"]
    time_of_day: str | None = None
    timezone: str = "America/New_York"
    is_enabled: bool = True


class ActivateDatasourceRequest(CamelModel):
    draft_id: uuid.UUID
    mapping: ActivateMapping
    schedule: ActivateSchedule


class ActivateDatasourceResponse(CamelModel):
    datasource_id: uuid.UUID
    status: str
