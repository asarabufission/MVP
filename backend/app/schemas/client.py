import uuid
from datetime import datetime
from typing import Literal

from app.schemas.common import CamelModel


class ClientCreateRequest(CamelModel):
    name: str
    description: str | None = None
    default_identifier_type: str
    default_identifier_value: str


class ClientPatchRequest(CamelModel):
    name: str | None = None
    description: str | None = None
    default_identifier_type: str | None = None
    default_identifier_value: str | None = None


class IdentifierOverrideRequest(CamelModel):
    identifier_type: str
    identifier_value: str


class AssignmentCreateRequest(CamelModel):
    datasource_id: uuid.UUID
    identifier_type: str | None = None
    identifier_value: str | None = None


class ClientListItem(CamelModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    default_identifier_type: str
    default_identifier_value: str
    readiness: str
    assigned_count: int
    billing_source_name: str | None = None
    identity_anchor_name: str | None = None
    created_at: datetime


class ClientListResponse(CamelModel):
    items: list[ClientListItem]
    next_cursor: str | None = None
    total_count: int


class ClientAssignmentItem(CamelModel):
    id: uuid.UUID
    datasource_id: uuid.UUID
    datasource_name: str
    category: str
    source_type: str
    scope: str
    datasource_status: str
    is_billing_source: bool
    is_identity_anchor: bool
    identifier_type: str | None = None
    identifier_value: str | None = None
    effective_identifier_type: str
    effective_identifier_value: str
    status: Literal["ACTIVE", "INACTIVE"]
    assigned_at: datetime
    inactivated_at: datetime | None = None


class ClientDetailResponse(CamelModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    default_identifier_type: str
    default_identifier_value: str
    readiness: str
    assigned_count: int
    billing_source_name: str | None = None
    identity_anchor_name: str | None = None
    created_at: datetime
    updated_at: datetime
    assignments: list[ClientAssignmentItem]
