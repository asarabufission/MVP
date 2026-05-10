import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.datasource import Datasource
from app.models.job_run import JobRun
from app.models.report_run import ReportRun
from app.schemas.dashboard import (
    DashboardSummary,
    FailedRunItem,
    RecentActivityItem,
)


async def build_summary(db: AsyncSession, msp_id: uuid.UUID) -> DashboardSummary:
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    forty_eight_hours_ago = now - timedelta(hours=48)

    clients_ready = await db.scalar(
        select(func.count())
        .select_from(Client)
        .where(Client.msp_id == msp_id, Client.readiness == "READY")
    ) or 0

    total_clients = await db.scalar(
        select(func.count()).select_from(Client).where(Client.msp_id == msp_id)
    ) or 0

    active_datasources = await db.scalar(
        select(func.count())
        .select_from(Datasource)
        .where(Datasource.msp_id == msp_id, Datasource.status == "ACTIVE")
    ) or 0

    total_datasources = await db.scalar(
        select(func.count())
        .select_from(Datasource)
        .where(Datasource.msp_id == msp_id)
    ) or 0

    recent_runs_count = await db.scalar(
        select(func.count())
        .select_from(JobRun)
        .where(JobRun.msp_id == msp_id, JobRun.started_at >= seven_days_ago)
    ) or 0

    reports_generated = await db.scalar(
        select(func.count())
        .select_from(ReportRun)
        .where(ReportRun.msp_id == msp_id, ReportRun.status == "READY")
    ) or 0

    failed_rows = (
        await db.execute(
            select(
                JobRun.id,
                JobRun.error_message,
                JobRun.started_at,
                Datasource.name.label("datasource_name"),
            )
            .join(Datasource, Datasource.id == JobRun.datasource_id, isouter=True)
            .where(
                JobRun.msp_id == msp_id,
                JobRun.status == "FAILED",
                JobRun.started_at >= forty_eight_hours_ago,
            )
            .order_by(JobRun.started_at.desc())
            .limit(5)
        )
    ).all()

    failed_runs = [
        FailedRunItem(
            id=row.id,
            datasource_name=row.datasource_name,
            error=row.error_message,
            started_at=row.started_at,
        )
        for row in failed_rows
    ]

    recent_rows = (
        await db.execute(
            select(
                JobRun.id,
                JobRun.status,
                JobRun.job_type,
                JobRun.started_at,
                JobRun.ended_at,
                JobRun.records_count,
                Datasource.name.label("datasource_name"),
                Client.name.label("client_name"),
            )
            .join(Datasource, Datasource.id == JobRun.datasource_id, isouter=True)
            .join(Client, Client.id == JobRun.client_id, isouter=True)
            .where(JobRun.msp_id == msp_id)
            .order_by(JobRun.started_at.desc())
            .limit(10)
        )
    ).all()

    recent_activity = [
        RecentActivityItem(
            id=row.id,
            status=row.status,
            datasource_name=row.datasource_name,
            client_name=row.client_name,
            type=row.job_type,
            started_at=row.started_at,
            ended_at=row.ended_at,
            records=row.records_count,
        )
        for row in recent_rows
    ]

    return DashboardSummary(
        clients_ready=clients_ready,
        total_clients=total_clients,
        active_datasources=active_datasources,
        total_datasources=total_datasources,
        recent_runs_count=recent_runs_count,
        reports_generated=reports_generated,
        failed_runs=failed_runs,
        recent_activity=recent_activity,
    )
