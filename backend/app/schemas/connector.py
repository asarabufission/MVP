from typing import Any

from app.schemas.common import CamelModel


class CredentialSchemaField(CamelModel):
    key: str
    label: str
    type: str
    required: bool = True
    default: str | None = None
    hint: str | None = None


class ConnectorListItem(CamelModel):
    source_id: str
    display_name: str
    category: str
    source_type: str
    scope_default: str
    auth_type: str
    description: str


class ConnectorDetailResponse(CamelModel):
    source_id: str
    display_name: str
    category: str
    source_type: str
    scope_default: str
    auth_type: str
    description: str
    credential_schema: list[CredentialSchemaField]
    default_field_mappings: dict[str, str]


class BlueprintDetails(CamelModel):
    credential_schema: list[dict[str, Any]]
    default_field_mappings: dict[str, str]
    category: str
    source_type: str
    scope: str
    display_name: str | None = None
