import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    DatasourceNotFoundError,
    DraftNotFoundError,
    NotImplementedActivationError,
    SchemaHashMismatchError,
)
from app.db.session import AsyncSessionLocal
from app.models.client import Client
from app.models.client_datasource_assignment import ClientDatasourceAssignment
from app.models.datasource import Datasource
from app.models.datasource_draft import DatasourceDraft
from app.models.datasource_schedule import DatasourceSchedule
from app.models.job_run import JobRun
from app.models.user import User
from app.services.aws_clients import localstack_client
from app.services.connector_service import get_connector
from app.services.datasource_draft_service import _preview_cache_key
from app.services.mapping_service import validate_field_mappings, write_mapping_document
from app.services.redis_client import cache_get


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# list datasources for the MSP whether active or inactive
async def list_datasources(
    db: AsyncSession,
    msp_id: uuid.UUID,
    *,
    status: str | None = None,
    client_id: uuid.UUID | None = None,
    include_inactive: bool = False,
) -> list[Datasource]:
    stmt = select(Datasource).where(Datasource.msp_id == msp_id)
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        stmt = stmt.where(Datasource.status.in_(statuses))
    elif not include_inactive:
        stmt = stmt.where(Datasource.status != "INACTIVE")

    if client_id is not None:
        assigned_ids = select(ClientDatasourceAssignment.datasource_id).where(
            ClientDatasourceAssignment.client_id == client_id,
            ClientDatasourceAssignment.msp_id == msp_id,
            ClientDatasourceAssignment.status == "ACTIVE",
        )
        stmt = stmt.where(
            (Datasource.client_id == client_id) | (Datasource.id.in_(assigned_ids))
        )

    stmt = stmt.order_by(Datasource.category, Datasource.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_datasource(
    db: AsyncSession, msp_id: uuid.UUID, datasource_id: uuid.UUID
) -> tuple[Datasource, DatasourceSchedule | None, Client | None]:
    result = await db.execute(
        select(Datasource).where(
            Datasource.id == datasource_id,
            Datasource.msp_id == msp_id,
        )
    )
    ds = result.scalar_one_or_none()
    if ds is None:
        raise DatasourceNotFoundError()

    sched_result = await db.execute(
        select(DatasourceSchedule).where(DatasourceSchedule.datasource_id == ds.id)
    )
    schedule = sched_result.scalar_one_or_none()

    client = None
    if ds.client_id:
        client_result = await db.execute(select(Client).where(Client.id == ds.client_id))
        client = client_result.scalar_one_or_none()

    return ds, schedule, client


async def patch_datasource(
    db: AsyncSession,
    msp_id: uuid.UUID,
    datasource_id: uuid.UUID,
    *,
    name: str | None = None,
    config: dict[str, Any] | None = None,
    schedule_patch: dict[str, Any] | None = None,
) -> tuple[Datasource, DatasourceSchedule | None, Client | None]:
    ds, schedule, client = await get_datasource(db, msp_id, datasource_id)
    if name is not None:
        ds.name = name
    if config is not None:
        ds.config = config

    if schedule_patch:
        if schedule is None:
            schedule = DatasourceSchedule(
                datasource_id=ds.id,
                frequency=schedule_patch.get("frequency", "MANUAL"),
                time_of_day=schedule_patch.get("time_of_day"),
                timezone=schedule_patch.get("timezone", "America/New_York"),
                is_enabled=schedule_patch.get("is_enabled", True),
            )
            db.add(schedule)
        else:
            if "frequency" in schedule_patch:
                schedule.frequency = schedule_patch["frequency"]
            if "time_of_day" in schedule_patch:
                schedule.time_of_day = schedule_patch["time_of_day"]
            if "timezone" in schedule_patch:
                schedule.timezone = schedule_patch["timezone"]
            if "is_enabled" in schedule_patch:
                schedule.is_enabled = schedule_patch["is_enabled"]

    await db.flush()
    return ds, schedule, client


async def soft_delete_datasource(
    db: AsyncSession,
    msp_id: uuid.UUID,
    user_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> Datasource:
    """Soft delete: set status INACTIVE and cascade to active assignments."""
    ds, _, _ = await get_datasource(db, msp_id, datasource_id)
    if ds.status == "INACTIVE":
        return ds
    await inactivate_datasource(db, msp_id, user_id, datasource_id)
    await db.refresh(ds)
    return ds


async def inactivate_datasource(
    db: AsyncSession,
    msp_id: uuid.UUID,
    user_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> None:
    ds, _, _ = await get_datasource(db, msp_id, datasource_id)
    now = datetime.now(timezone.utc)
    ds.status = "INACTIVE"
    ds.inactivated_at = now
    ds.inactivated_by = user_id

    await db.execute(
        update(ClientDatasourceAssignment)
        .where(
            ClientDatasourceAssignment.datasource_id == datasource_id,
            ClientDatasourceAssignment.msp_id == msp_id,
            ClientDatasourceAssignment.status == "ACTIVE",
        )
        .values(
            status="INACTIVE",
            inactivated_at=now,
            inactivated_by=user_id,
        )
    )
    await db.flush()


async def reactivate_datasource(
    db: AsyncSession,
    msp_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> None:
    ds, _, _ = await get_datasource(db, msp_id, datasource_id)
    ds.status = "ACTIVE"
    ds.inactivated_at = None
    ds.inactivated_by = None
    await db.flush()


async def _run_activation_background(
    datasource_id: uuid.UUID,
    msp_id: uuid.UUID,
    *,
    category: str,
    schema_hash: str,
    field_mappings: list[dict[str, Any]],
    additional_params: list[dict[str, Any]] | None,
    sample_rows: list[dict[str, Any]],
) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Datasource).where(Datasource.id == datasource_id))
        ds = result.scalar_one()
        job_result = await db.execute(
            select(JobRun)
            .where(
                JobRun.datasource_id == datasource_id,
                JobRun.job_type == "ACTIVATION",
                JobRun.status == "RUNNING",
            )
            .order_by(JobRun.started_at.desc())
            .limit(1)
        )
        job = job_result.scalar_one_or_none()

        try:
            write_mapping_document(
                datasource_id,
                category=category,
                schema_hash=schema_hash,
                field_mappings=field_mappings,
                additional_params=additional_params,
            )

            landing_key = (
                f"{settings.S3_LANDING_PREFIX}/msp_id={msp_id}/"
                f"datasource_id={datasource_id}/run_id=activation/data.json"
            )
            s3 = localstack_client("s3")
            s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=landing_key,
                Body=json.dumps({"records": sample_rows}, indent=2).encode(),
                ContentType="application/json",
            )
            landing_path = f"s3://{settings.S3_BUCKET}/{landing_key}"
            glue_table = f"ds_{_slug(ds.name)}_{str(datasource_id)[:8]}"

            glue = localstack_client("glue")
            try:
                glue.get_database(Name=settings.GLUE_DATABASE)
            except Exception:
                glue.create_database(DatabaseInput={"Name": settings.GLUE_DATABASE})

            try:
                glue.create_table(
                    DatabaseName=settings.GLUE_DATABASE,
                    TableInput={
                        "Name": glue_table,
                        "StorageDescriptor": {
                            "Columns": [{"Name": "payload", "Type": "string"}],
                            "Location": f"s3://{settings.S3_BUCKET}/{settings.S3_LANDING_PREFIX}/",
                            "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                            "SerdeInfo": {
                                "SerializationLibrary": (
                                    "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
                                )
                            },
                        },
                        "TableType": "EXTERNAL_TABLE",
                    },
                )
            except Exception:
                pass

            ds.status = "ACTIVE"
            ds.landing_path = landing_path
            ds.glue_table_name = glue_table
            if job:
                job.status = "SUCCESS"
                job.ended_at = datetime.now(timezone.utc)
                job.landing_s3_path = landing_path
                job.glue_table_name = glue_table
                job.records_count = len(sample_rows)
        except Exception as exc:
            ds.status = "DEGRADED"
            if job:
                job.status = "FAILED"
                job.ended_at = datetime.now(timezone.utc)
                job.error_message = str(exc)[:500]
        await db.commit()


async def activate_datasource(
    db: AsyncSession,
    user: User,
    *,
    draft_id: uuid.UUID,
    mapping: dict[str, Any],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    draft_result = await db.execute(
        select(DatasourceDraft).where(
            DatasourceDraft.id == draft_id,
            DatasourceDraft.msp_id == user.msp_id,
            DatasourceDraft.status == "DRAFT",
        )
    )
    draft = draft_result.scalar_one_or_none()
    if draft is None:
        raise DraftNotFoundError()

    if draft.category == "RECONCILIATION":
        raise NotImplementedActivationError()

    preview = await cache_get(_preview_cache_key(draft_id))
    if preview is None and not draft.schema_hash:
        raise SchemaHashMismatchError("Schema preview has expired; run test connection again")

    submitted_hash = mapping.get("schema_hash")
    active_hash = (preview or {}).get("schema_hash") or draft.schema_hash
    if submitted_hash != active_hash:
        raise SchemaHashMismatchError()

    field_mappings = mapping.get("field_mappings") or []
    validate_field_mappings(draft.category, field_mappings)

    blueprint = await get_connector(draft.blueprint_id or "custom")
    sample_rows = (preview or {}).get("sample_rows") or blueprint.get("sample_rows", [])
    additional_params = mapping.get("additional_params") or []
    config = (draft.draft_payload or {}).get("config") or {}

    permanent_secret = draft.secret_arn or (
        f"arn:aws:secretsmanager:{settings.AWS_REGION}:000000000000:secret:"
        f"{settings.SECRETS_PREFIX}/datasource/{draft_id}"
    )

    ds = Datasource(
        msp_id=user.msp_id,
        draft_id=draft.id,
        client_id=draft.client_id,
        blueprint_id=draft.blueprint_id,
        name=draft.display_name or draft.name,
        vendor=draft.vendor,
        category=draft.category,
        source_type=draft.source_type,
        scope=draft.scope,
        status="ACTIVATING",
        secret_arn=permanent_secret,
        schema_hash=active_hash,
        config=config,
    )
    db.add(ds)
    await db.flush()

    sched = DatasourceSchedule(
        datasource_id=ds.id,
        frequency=schedule.get("frequency", "MANUAL"),
        time_of_day=schedule.get("time_of_day"),
        timezone=schedule.get("timezone", "America/New_York"),
        is_enabled=schedule.get("is_enabled", True),
    )
    db.add(sched)

    if draft.client_id:
        existing = await db.execute(
            select(ClientDatasourceAssignment).where(
                ClientDatasourceAssignment.client_id == draft.client_id,
                ClientDatasourceAssignment.datasource_id == ds.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                ClientDatasourceAssignment(
                    msp_id=user.msp_id,
                    client_id=draft.client_id,
                    datasource_id=ds.id,
                    assigned_by=user.id,
                    status="ACTIVE",
                )
            )

    activation_job = JobRun(
        msp_id=user.msp_id,
        datasource_id=ds.id,
        client_id=draft.client_id,
        job_type="ACTIVATION",
        status="RUNNING",
        started_at=datetime.now(timezone.utc),
    )
    db.add(activation_job)

    draft.status = "ACTIVATED"
    await db.flush()

    return {
        "datasource_id": ds.id,
        "status": ds.status,
        "background": {
            "category": draft.category,
            "schema_hash": active_hash,
            "field_mappings": field_mappings,
            "additional_params": additional_params,
            "sample_rows": sample_rows,
        },
    }


async def run_activation_background_from_result(
    datasource_id: uuid.UUID,
    msp_id: uuid.UUID,
    background: dict[str, Any],
) -> None:
    await _run_activation_background(
        datasource_id,
        msp_id,
        category=background["category"],
        schema_hash=background["schema_hash"],
        field_mappings=background["field_mappings"],
        additional_params=background["additional_params"],
        sample_rows=background["sample_rows"],
    )
