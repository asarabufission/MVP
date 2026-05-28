import uuid
from typing import Any

from app.core.config import settings
from app.services.aws_clients import localstack_client

LICENSING_STANDARD_FIELDS = [
    {"standard_field": "user_email", "required": True, "data_type": "string"},
    {"standard_field": "first_name", "required": False, "data_type": "string"},
    {"standard_field": "last_name", "required": False, "data_type": "string"},
    {"standard_field": "license_type", "required": True, "data_type": "string_or_array"},
    {"standard_field": "is_licensed", "required": True, "data_type": "boolean"},
    {"standard_field": "department", "required": False, "data_type": "string"},
    {"standard_field": "record_date", "required": True, "data_type": "date"},
]

ENDPOINT_STANDARD_FIELDS = [
    {"standard_field": "device_hostname", "required": True, "data_type": "string"},
    {"standard_field": "device_description", "required": True, "data_type": "string"},
    {"standard_field": "record_date", "required": True, "data_type": "date"},
    {"standard_field": "client_identifier", "required": True, "data_type": "string"},
    {"standard_field": "last_seen_at", "required": False, "data_type": "timestamp"},
    {"standard_field": "serial_number", "required": False, "data_type": "string"},
    {"standard_field": "device_type", "required": False, "data_type": "string"},
    {"standard_field": "site_name", "required": False, "data_type": "string"},
]


def standard_fields_for_category(category: str) -> list[dict[str, Any]]:
    if category == "ENDPOINT":
        return ENDPOINT_STANDARD_FIELDS
    return LICENSING_STANDARD_FIELDS


def required_standard_fields(category: str) -> set[str]:
    return {
        f["standard_field"]
        for f in standard_fields_for_category(category)
        if f["required"]
    }


def validate_field_mappings(
    category: str,
    field_mappings: list[dict[str, Any]],
) -> None:
    from app.core.exceptions import RequiredMappingMissingError

    mapped = {m["standard_field"]: m.get("source_field") for m in field_mappings}
    missing = [
        f
        for f in required_standard_fields(category)
        if not mapped.get(f)
    ]
    if missing:
        raise RequiredMappingMissingError(
            f"Missing required mappings: {', '.join(missing)}"
        )


def write_mapping_document(
    datasource_id: uuid.UUID,
    *,
    category: str,
    schema_hash: str,
    field_mappings: list[dict[str, Any]],
    additional_params: list[dict[str, Any]] | None = None,
) -> None:
    table = localstack_client("dynamodb")
    item = {
        "pk": {"S": f"DATASOURCE#{datasource_id}"},
        "sk": {"S": "MAPPING#v1"},
        "category": {"S": category},
        "schema_hash": {"S": schema_hash},
        "field_mappings": {"S": str(field_mappings)},
        "additional_params": {"S": str(additional_params or [])},
    }
    table.put_item(TableName=settings.DYNAMODB_TABLE, Item=item)
