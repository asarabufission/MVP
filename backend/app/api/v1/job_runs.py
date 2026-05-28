from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job_run import JobRunListItem
from app.services import job_run_service

router = APIRouter()


@router.get("", response_model=list[JobRunListItem])
async def list_job_runs_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    status: str = Query(default="ALL"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobRunListItem]:
    rows = await job_run_service.list_job_runs(
        db,
        user.msp_id,
        limit=limit,
        status=status if status != "ALL" else None,
    )
    return [JobRunListItem(**row) for row in rows]
