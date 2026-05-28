import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.roles import require_role
from app.models.user import User
from app.schemas.datasource import (
    ActivateDatasourceRequest,
    ActivateDatasourceResponse,
    DatasourceDeleteResponse,
    DatasourceDetailResponse,
    DatasourceListItem,
    DatasourceListResponse,
    DatasourcePatchRequest,
    DatasourceScheduleResponse,
)
from app.services import datasource_service

router = APIRouter()


def _list_item(ds) -> DatasourceListItem:
    return DatasourceListItem(
        id=ds.id,
        name=ds.name,
        vendor=ds.vendor,
        category=ds.category,
        source_type=ds.source_type,
        scope=ds.scope,
        status=ds.status,
        last_run_at=ds.last_run_at,
        created_at=ds.created_at,
        updated_at=ds.updated_at,
        inactivated_at=ds.inactivated_at,
        client_id=ds.client_id,
        blueprint_id=ds.blueprint_id,
    )


def _detail(ds, schedule, client) -> DatasourceDetailResponse:
    sched_resp = None
    if schedule is not None:
        sched_resp = DatasourceScheduleResponse(
            frequency=schedule.frequency,
            time_of_day=schedule.time_of_day,
            timezone=schedule.timezone,
            is_enabled=schedule.is_enabled,
        )
    return DatasourceDetailResponse(
        id=ds.id,
        name=ds.name,
        vendor=ds.vendor,
        category=ds.category,
        source_type=ds.source_type,
        scope=ds.scope,
        status=ds.status,
        blueprint_id=ds.blueprint_id,
        client_id=ds.client_id,
        client_name=client.name if client else None,
        config=ds.config,
        schema_hash=ds.schema_hash,
        landing_path=ds.landing_path,
        glue_table_name=ds.glue_table_name,
        last_run_at=ds.last_run_at,
        created_at=ds.created_at,
        updated_at=ds.updated_at,
        inactivated_at=ds.inactivated_at,
        schedule=sched_resp,
    )


@router.get("", response_model=DatasourceListResponse)
async def list_datasources_endpoint(
    status: str | None = Query(
        default=None,
        description="Comma-separated statuses, e.g. ACTIVE,INACTIVE",
    ),
    client_id: uuid.UUID | None = Query(default=None),
    include_inactive: bool = Query(
        default=False,
        alias="includeInactive",
        description="When true, returns all datasources including soft-deleted (INACTIVE)",
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasourceListResponse:
    """Fetch all datasources for the MSP from PostgreSQL."""
    rows = await datasource_service.list_datasources(
        db,
        user.msp_id,
        status=status,
        client_id=client_id,
        include_inactive=include_inactive,
    )
    items = [_list_item(r) for r in rows]
    return DatasourceListResponse(items=items, total_count=len(items))


@router.get("/{datasource_id}", response_model=DatasourceDetailResponse)
async def get_datasource_endpoint(
    datasource_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasourceDetailResponse:
    """Fetch one datasource by id (includes INACTIVE / soft-deleted rows)."""
    ds, schedule, client = await datasource_service.get_datasource(
        db, user.msp_id, datasource_id
    )
    return _detail(ds, schedule, client)


@router.delete("/{datasource_id}", response_model=DatasourceDeleteResponse)
async def delete_datasource_endpoint(
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> DatasourceDeleteResponse:
    """
    Soft delete: sets status to INACTIVE (row stays in PostgreSQL).
    Also inactivates active client assignments for this datasource.
    """
    ds = await datasource_service.soft_delete_datasource(
        db, user.msp_id, user.id, datasource_id
    )
    return DatasourceDeleteResponse(
        id=ds.id,
        status=ds.status,
        inactivated_at=ds.inactivated_at,
    )


@router.patch("/{datasource_id}", response_model=DatasourceDetailResponse)
async def patch_datasource_endpoint(
    datasource_id: uuid.UUID,
    payload: DatasourcePatchRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> DatasourceDetailResponse:
    schedule_patch = None
    if payload.schedule is not None:
        schedule_patch = payload.schedule.model_dump()
    ds, schedule, client = await datasource_service.patch_datasource(
        db,
        user.msp_id,
        datasource_id,
        name=payload.name,
        config=payload.config,
        schedule_patch=schedule_patch,
    )
    return _detail(ds, schedule, client)


@router.patch("/{datasource_id}/inactivate", status_code=204)
async def inactivate_datasource_endpoint(
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Alias for soft delete (SPEC-compatible). Prefer DELETE for CRUD."""
    await datasource_service.soft_delete_datasource(
        db, user.msp_id, user.id, datasource_id
    )
    return Response(status_code=204)


@router.patch("/{datasource_id}/reactivate", status_code=204)
async def reactivate_datasource_endpoint(
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await datasource_service.reactivate_datasource(
        db, user.msp_id, datasource_id
    )
    return Response(status_code=204)


@router.post("/activate", response_model=ActivateDatasourceResponse, status_code=202)
async def activate_datasource_endpoint(
    payload: ActivateDatasourceRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ActivateDatasourceResponse:
    field_mappings = [m.model_dump() for m in payload.mapping.field_mappings]
    result = await datasource_service.activate_datasource(
        db,
        user,
        draft_id=payload.draft_id,
        mapping={
            "schema_hash": payload.mapping.schema_hash,
            "field_mappings": field_mappings,
            "additional_params": payload.mapping.additional_params,
        },
        schedule=payload.schedule.model_dump(),
    )
    background = result.pop("background")
    await db.commit()
    await datasource_service.run_activation_background_from_result(
        result["datasource_id"],
        user.msp_id,
        background,
    )
    ds, _, _ = await datasource_service.get_datasource(
        db, user.msp_id, result["datasource_id"]
    )
    return ActivateDatasourceResponse(
        datasource_id=result["datasource_id"],
        status=ds.status,
    )
