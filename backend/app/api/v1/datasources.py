from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.datasource import Datasource
from app.models.user import User
from app.schemas.datasource import DatasourceListItem, DatasourceListResponse

router = APIRouter()


@router.get("", response_model=DatasourceListResponse)
async def list_datasources_endpoint(
    status: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasourceListResponse:
    stmt = select(Datasource).where(Datasource.msp_id == user.msp_id)
    if status:
        stmt = stmt.where(Datasource.status == status)
    stmt = stmt.order_by(Datasource.category, Datasource.name)

    rows = (await db.execute(stmt)).scalars().all()
    items = [
        DatasourceListItem(
            id=r.id,
            name=r.name,
            vendor=r.vendor,
            category=r.category,
            source_type=r.source_type,
            scope=r.scope,
            status=r.status,
            last_run_at=r.last_run_at,
            created_at=r.created_at,
            client_id=r.client_id,
            blueprint_id=r.blueprint_id,
        )
        for r in rows
    ]
    return DatasourceListResponse(items=items, total_count=len(items))
