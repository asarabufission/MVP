import json
from typing import Any

from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import ConnectorNotFoundError
from app.data.connector_blueprints import BLUEPRINTS
from app.services.aws_clients import localstack_client
from app.services.redis_client import cache_get, cache_set

_CACHE_TTL = 300
_CACHE_KEY_ALL = "connectors:all"
_CACHE_KEY_ONE = "connectors:one:"


def _normalize_blueprint(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": raw["source_id"],
        "display_name": raw.get("display_name", raw["source_id"]),
        "category": raw["category"],
        "source_type": raw.get("source_type", "API"),
        "scope_default": raw.get("scope_default", "MSP_LEVEL"),
        "auth_type": raw.get("auth_type", "api_key"),
        "description": raw.get("description", ""),
        "credential_schema": raw.get("credential_schema", []),
        "default_field_mappings": raw.get("default_field_mappings", {}),
        "sample_rows": raw.get("sample_rows", []),
    }


def _builtin_by_id(source_id: str) -> dict[str, Any] | None:
    for bp in BLUEPRINTS:
        if bp["source_id"] == source_id:
            return _normalize_blueprint(bp)
    return None


def _builtin_all() -> list[dict[str, Any]]:
    return [_normalize_blueprint(bp) for bp in BLUEPRINTS]


def _dynamo_get(source_id: str) -> dict[str, Any] | None:
    table = localstack_client("dynamodb")
    try:
        resp = table.get_item(
            TableName=settings.DYNAMODB_CONNECTOR_REGISTRY_TABLE,
            Key={"source_id": {"S": source_id}},
        )
    except ClientError:
        return None
    item = resp.get("Item")
    if not item:
        return None
    raw = {k: _ddb_val(v) for k, v in item.items()}
    return _normalize_blueprint(raw)


def _ddb_val(node: dict) -> Any:
    if "S" in node:
        return node["S"]
    if "N" in node:
        return node["N"]
    if "BOOL" in node:
        return node["BOOL"]
    if "M" in node:
        return {k: _ddb_val(v) for k, v in node["M"].items()}
    if "L" in node:
        return [_ddb_val(v) for v in node["L"]]
    if "NULL" in node:
        return None
    return None


def _dynamo_scan_all() -> list[dict[str, Any]] | None:
    table = localstack_client("dynamodb")
    try:
        resp = table.scan(TableName=settings.DYNAMODB_CONNECTOR_REGISTRY_TABLE)
    except ClientError:
        return None
    items = resp.get("Items") or []
    if not items:
        return None
    return [_normalize_blueprint({k: _ddb_val(v) for k, v in item.items()}) for item in items]


async def list_connectors() -> list[dict[str, Any]]:
    cached = await cache_get(_CACHE_KEY_ALL)
    if cached is not None:
        return cached["items"]

    items = _dynamo_scan_all() or _builtin_all()
    await cache_set(_CACHE_KEY_ALL, {"items": items}, _CACHE_TTL)
    return items


async def get_connector(source_id: str) -> dict[str, Any]:
    cache_key = f"{_CACHE_KEY_ONE}{source_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    blueprint = _dynamo_get(source_id) or _builtin_by_id(source_id)
    if blueprint is None:
        raise ConnectorNotFoundError()
    await cache_set(cache_key, blueprint, _CACHE_TTL)
    return blueprint


def blueprint_details_for_draft(blueprint: dict[str, Any]) -> dict[str, Any]:
    return {
        "credential_schema": blueprint.get("credential_schema", []),
        "default_field_mappings": blueprint.get("default_field_mappings", {}),
        "category": blueprint["category"],
        "source_type": blueprint.get("source_type", "API"),
        "scope": blueprint.get("scope_default", "MSP_LEVEL"),
        "display_name": blueprint.get("display_name"),
    }


def seed_connector_registry() -> None:
    table = localstack_client("dynamodb")
    for bp in BLUEPRINTS:
        item = {
            "source_id": {"S": bp["source_id"]},
            "display_name": {"S": bp["display_name"]},
            "category": {"S": bp["category"]},
            "source_type": {"S": bp["source_type"]},
            "scope_default": {"S": bp["scope_default"]},
            "auth_type": {"S": bp["auth_type"]},
            "description": {"S": bp["description"]},
            "credential_schema": {"S": json.dumps(bp["credential_schema"])},
            "default_field_mappings": {"S": json.dumps(bp["default_field_mappings"])},
        }
        try:
            table.put_item(
                TableName=settings.DYNAMODB_CONNECTOR_REGISTRY_TABLE,
                Item=item,
            )
        except ClientError:
            pass
