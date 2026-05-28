import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.datasource import Datasource
from app.models.job_run import JobRun


async def list_job_runs(
    db: AsyncSession,
    msp_id: uuid.UUID,
    *,
    limit: int = 50,
    status: str | None = None,
) -> list[dict]:
    stmt = (
        select(
            JobRun.id,
            JobRun.status,
            JobRun.job_type,
            JobRun.started_at,
            JobRun.ended_at,
            JobRun.records_count,
            JobRun.error_message,
            Datasource.name.label("datasource_name"),
            Client.name.label("client_name"),
        )
        .join(Datasource, Datasource.id == JobRun.datasource_id, isouter=True)
        .join(Client, Client.id == JobRun.client_id, isouter=True)
        .where(JobRun.msp_id == msp_id)
        .order_by(JobRun.started_at.desc())
        .limit(min(limit, 200))
    )

    if status and status.upper() != "ALL":
        stmt = stmt.where(JobRun.status == status.upper())

    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": row.id,
            "status": row.status,
            "datasource_name": row.datasource_name,
            "client_name": row.client_name,
            "job_type": row.job_type,
            "started_at": row.started_at,
            "ended_at": row.ended_at,
            "records": row.records_count,
            "error_message": row.error_message,
        }
        for row in rows
    ]
