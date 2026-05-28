import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConnectorNotFoundError,
    DraftNotFoundError,
    PreviewExpiredError,
    SecretsManagerError,
    VendorAuthFailedError,
)
from app.models.client import Client
from app.models.datasource_draft import DatasourceDraft
from app.models.job_run import JobRun
from app.models.user import User
from app.services.aws_clients import localstack_client
from app.services.connector_service import blueprint_details_for_draft, get_connector
from app.services.mapping_service import standard_fields_for_category
from app.services.redis_client import cache_get, cache_set

PREVIEW_TTL_SECONDS = 30 * 60


def _preview_cache_key(draft_id: uuid.UUID) -> str:
    return f"datasource:schema-preview:{draft_id}"


def _idempotency_key(draft_id: uuid.UUID, credentials: dict[str, Any]) -> str:
    payload = json.dumps(credentials, sort_keys=True)
    digest = hashlib.sha256(f"{draft_id}:{payload}".encode()).hexdigest()
    return f"datasource:test-connection:{digest}"


def _infer_fields(sample_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not sample_rows:
        return []
    keys: set[str] = set()
    for row in sample_rows:
        keys.update(row.keys())
    fields = []
    for name in sorted(keys):
        sample_values = [row.get(name) for row in sample_rows[:5] if name in row]
        value_type = "string"
        if sample_values and isinstance(sample_values[0], bool):
            value_type = "boolean"
        elif sample_values and isinstance(sample_values[0], (int, float)):
            value_type = "number"
        fields.append(
            {
                "name": name,
                "type": value_type,
                "nullable": True,
                "sample_values": sample_values[:3],
            }
        )
    return fields


def _schema_hash(fields: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        [{"name": f["name"], "type": f["type"]} for f in fields],
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


async def _load_client(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID
) -> Client | None:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.msp_id == msp_id)
    )
    return result.scalar_one_or_none()


async def _load_draft(
    db: AsyncSession, msp_id: uuid.UUID, draft_id: uuid.UUID
) -> DatasourceDraft | None:
    result = await db.execute(
        select(DatasourceDraft).where(
            DatasourceDraft.id == draft_id,
            DatasourceDraft.msp_id == msp_id,
            DatasourceDraft.status == "DRAFT",
        )
    )
    return result.scalar_one_or_none()


def _store_draft_credentials(draft_id: uuid.UUID, credentials: dict[str, Any]) -> str:
    secret_name = f"{settings.SECRETS_PREFIX}/datasource-draft/{draft_id}"
    sm = localstack_client("secretsmanager")
    secret_string = json.dumps(credentials)
    try:
        sm.create_secret(Name=secret_name, SecretString=secret_string)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("ResourceExistsException",):
            sm.put_secret_value(SecretId=secret_name, SecretString=secret_string)
        else:
            raise SecretsManagerError() from exc
    return f"arn:aws:secretsmanager:{settings.AWS_REGION}:000000000000:secret:{secret_name}"


def _write_sample_to_s3(
    draft_id: uuid.UUID, attempt_id: uuid.UUID, sample_rows: list[dict[str, Any]]
) -> str:
    key = f"{settings.S3_TMP_PREFIX}/{draft_id}/{attempt_id}/sample.json"
    s3 = localstack_client("s3")
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=json.dumps(sample_rows, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return key


async def create_draft(
    db: AsyncSession,
    user: User,
    *,
    client_id: uuid.UUID,
    blueprint_id: str,
    name: str | None = None,
    display_name: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if blueprint_id == "csv_upload":
        raise ConnectorNotFoundError("CSV Upload is not implemented in this POC")

    blueprint = await get_connector(blueprint_id)
    client = await _load_client(db, user.msp_id, client_id)
    if client is None:
        return None

    resolved_name = name or blueprint["display_name"]
    details = blueprint_details_for_draft(blueprint)
    draft = DatasourceDraft(
        msp_id=user.msp_id,
        created_by=user.id,
        client_id=client_id,
        blueprint_id=blueprint_id,
        name=resolved_name,
        display_name=display_name or blueprint["display_name"],
        vendor=blueprint["display_name"],
        category=details["category"],
        source_type=details["source_type"],
        scope=details["scope"],
        status="DRAFT",
        current_step=1,
        draft_payload={"config": config or {}},
    )
    db.add(draft)
    await db.flush()

    return {
        "draft_id": draft.id,
        "status": draft.status,
        "blueprint_details": details,
        "current_step": draft.current_step,
    }


async def test_connection(
    db: AsyncSession,
    msp_id: uuid.UUID,
    draft_id: uuid.UUID,
    *,
    credentials: dict[str, Any],
    attempt_id: uuid.UUID,
) -> dict[str, Any]:
    draft = await _load_draft(db, msp_id, draft_id)
    if draft is None:
        raise DraftNotFoundError()

    if not credentials:
        raise VendorAuthFailedError("Credentials are required")

    idem_key = _idempotency_key(draft_id, credentials)
    cached = await cache_get(idem_key)
    if cached is not None:
        cached["cached"] = True
        return cached

    blueprint = await get_connector(draft.blueprint_id or "custom")
    sample_rows = blueprint.get("sample_rows") or [{"record_date": datetime.now(timezone.utc).date().isoformat()}]
    fields = _infer_fields(sample_rows)
    schema_hash = _schema_hash(fields)

    secret_arn = _store_draft_credentials(draft_id, credentials)
    sample_s3_path = _write_sample_to_s3(draft_id, attempt_id, sample_rows)

    draft.secret_arn = secret_arn
    draft.schema_hash = schema_hash
    draft.sample_s3_path = sample_s3_path
    draft.last_attempt_id = attempt_id
    draft.current_step = 2

    test_run = JobRun(
        msp_id=msp_id,
        draft_id=draft_id,
        client_id=draft.client_id,
        job_type="TEST_CONNECTION",
        status="SUCCESS",
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        records_count=len(sample_rows),
    )
    db.add(test_run)
    await db.flush()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=PREVIEW_TTL_SECONDS)
    result = {
        "test_run_id": str(test_run.id),
        "schema_hash": schema_hash,
        "fields": fields,
        "sample_rows": sample_rows[:5],
        "record_count": len(sample_rows),
        "column_count": len(fields),
        "connection_time_ms": 120,
        "sample_s3_path": sample_s3_path,
        "cached": False,
        "expires_at": expires_at.isoformat(),
    }

    await cache_set(_preview_cache_key(draft_id), result, PREVIEW_TTL_SECONDS)
    await cache_set(idem_key, result, PREVIEW_TTL_SECONDS)
    return result


async def get_schema_preview(
    db: AsyncSession,
    msp_id: uuid.UUID,
    draft_id: uuid.UUID,
) -> dict[str, Any]:
    draft = await _load_draft(db, msp_id, draft_id)
    if draft is None:
        raise DraftNotFoundError()

    cached = await cache_get(_preview_cache_key(draft_id))
    if cached is not None:
        return {
            "fields": cached["fields"],
            "schema_hash": cached["schema_hash"],
            "sample_rows": cached["sample_rows"],
            "record_count": cached["record_count"],
            "column_count": cached["column_count"],
            "expires_at": cached.get("expires_at"),
            "standard_fields": standard_fields_for_category(draft.category),
        }

    if draft.schema_hash and draft.sample_s3_path:
        blueprint = await get_connector(draft.blueprint_id or "custom")
        sample_rows = blueprint.get("sample_rows", [])
        fields = _infer_fields(sample_rows)
        return {
            "fields": fields,
            "schema_hash": draft.schema_hash,
            "sample_rows": sample_rows[:5],
            "record_count": len(sample_rows),
            "column_count": len(fields),
            "expires_at": None,
            "standard_fields": standard_fields_for_category(draft.category),
        }

    raise PreviewExpiredError()
