import asyncio
import json
from datetime import datetime, timedelta, timezone

import bcrypt
from botocore.exceptions import ClientError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.client import Client
from app.models.client_datasource_assignment import ClientDatasourceAssignment
from app.models.datasource import Datasource
from app.models.job_run import JobRun
from app.models.msp import Msp
from app.models.user import User
from app.services.aws_clients import localstack_client
# from app.services.connector_service import seed_connector_registry


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

MSP_NAME = "MVP MSP"
MSP_EMAIL = "ops@mvp.com"

USERS = [
    {
        "username": "testmsp",
        "email": "testmsp@mvp.com",
        "password": "testmsp@123",
        "role": "MSP_ADMIN",
        "full_name": "Test MSP Admin",
    },
    {
        "username": "analyst",
        "email": "analyst@mvp.com",
        "password": "analyst@123",
        "role": "MSP_ANALYST",
        "full_name": "Demo Analyst",
    },
]

CLIENTS = [
    ("ERES Companies", "erescompanies.com"),
    ("Scoop Ride", "scoopride.io"),
    ("Pinnacle Legal", "pinnaclelegal.com"),
    ("Harbor View Medical", "harborviewmed.org"),
]

DATASOURCES = [
    ("M365 Production", "LICENSING", "API", "MSP_LEVEL", "ACTIVE"),
    ("Proofpoint Core", "LICENSING", "API", "MSP_LEVEL", "ACTIVE"),
    ("Ironscales", "LICENSING", "API", "MSP_LEVEL", "DEGRADED"),
    ("DropSuite", "LICENSING", "API", "MSP_LEVEL", "ACTIVE"),
    ("Datto RMM", "ENDPOINT", "API", "MSP_LEVEL", "ACTIVE"),
    ("SentinelOne", "ENDPOINT", "API", "MSP_LEVEL", "ACTIVE"),
    ("Autotask Billing", "RECONCILIATION", "API", "MSP_LEVEL", "ACTIVE"),
    ("ThreatLocker", "ENDPOINT", "API", "MSP_LEVEL", "DRAFT"),
]


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def _landing_path(msp_id, datasource_id) -> str:
    return (
        f"s3://{settings.S3_BUCKET}/{settings.S3_LANDING_PREFIX}/"
        f"msp_id={msp_id}/datasource_id={datasource_id}/run_id=seed/data.json"
    )


def _landing_key(msp_id, datasource_id) -> str:
    return (
        f"{settings.S3_LANDING_PREFIX}/"
        f"msp_id={msp_id}/datasource_id={datasource_id}/run_id=seed/data.json"
    )


async def seed_msp(session: AsyncSession) -> Msp:
    stmt = pg_insert(Msp).values(name=MSP_NAME, email=MSP_EMAIL)
    stmt = stmt.on_conflict_do_nothing(index_elements=["email"])
    await session.execute(stmt)
    await session.flush()
    result = await session.execute(select(Msp).where(Msp.email == MSP_EMAIL))
    return result.scalar_one()


async def seed_users(session: AsyncSession, msp_id) -> dict[str, User]:
    for u in USERS:
        stmt = pg_insert(User).values(
            msp_id=msp_id,
            username=u["username"],
            email=u["email"],
            password_hash=_hash_password(u["password"]),
            full_name=u["full_name"],
            role=u["role"],
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["email"])
        await session.execute(stmt)
    await session.flush()
    result = await session.execute(select(User).where(User.msp_id == msp_id))
    return {u.email: u for u in result.scalars().all()}


async def seed_clients(session: AsyncSession, msp_id) -> dict[str, Client]:
    for name, domain in CLIENTS:
        stmt = pg_insert(Client).values(
            msp_id=msp_id,
            name=name,
            default_identifier_type="EMAIL_DOMAIN_CONTAINS",
            default_identifier_value=domain,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["msp_id", "name"])
        await session.execute(stmt)
    await session.flush()
    result = await session.execute(select(Client).where(Client.msp_id == msp_id))
    return {c.name: c for c in result.scalars().all()}


async def seed_datasources(session: AsyncSession, msp_id) -> dict[str, Datasource]:
    result = await session.execute(select(Datasource).where(Datasource.msp_id == msp_id))
    existing = {d.name: d for d in result.scalars().all()}

    for name, category, source_type, scope, status in DATASOURCES:
        if name in existing:
            continue
        ds = Datasource(
            msp_id=msp_id,
            name=name,
            vendor=name,
            category=category,
            source_type=source_type,
            scope=scope,
            status=status,
            secret_arn=f"arn:aws:secretsmanager:us-east-1:000000000000:secret:msp-guardian/seed/{_slug(name)}",
        )
        session.add(ds)
    await session.flush()

    result = await session.execute(select(Datasource).where(Datasource.msp_id == msp_id))
    by_name = {d.name: d for d in result.scalars().all()}

    for vendor_name in ("Datto RMM", "SentinelOne"):
        ds = by_name[vendor_name]
        if ds.landing_path is None:
            ds.landing_path = _landing_path(msp_id, ds.id)
    await session.flush()

    return by_name


async def seed_assignments(
    session: AsyncSession,
    msp_id,
    admin_id,
    clients: dict[str, Client],
    datasources: dict[str, Datasource],
) -> None:
    matrix = [
        # ERES Companies
        ("ERES Companies", "M365 Production", None, None, False, True),
        ("ERES Companies", "Proofpoint Core", None, None, False, False),
        ("ERES Companies", "Ironscales", None, None, False, False),
        ("ERES Companies", "DropSuite", None, None, False, False),
        ("ERES Companies", "Datto RMM", "COMPANY_NAME_EQUALS", "ERES Companies Inc.", False, False),
        ("ERES Companies", "SentinelOne", "TENANT_ID_EQUALS", "eres-tnt-001", False, False),
        ("ERES Companies", "Autotask Billing", None, None, True, False),
        # Scoop Ride
        ("Scoop Ride", "M365 Production", None, None, False, True),
        ("Scoop Ride", "Proofpoint Core", None, None, False, False),
        ("Scoop Ride", "DropSuite", None, None, False, False),
        ("Scoop Ride", "Datto RMM", None, None, False, False),
        ("Scoop Ride", "Autotask Billing", None, None, True, False),
        # Pinnacle Legal
        ("Pinnacle Legal", "M365 Production", None, None, False, True),
        ("Pinnacle Legal", "Datto RMM", "COMPANY_NAME_EQUALS", "Pinnacle Legal LLP", False, False),
    ]
    for client_name, ds_name, id_type, id_value, is_billing, is_anchor in matrix:
        client = clients[client_name]
        ds = datasources[ds_name]
        stmt = pg_insert(ClientDatasourceAssignment).values(
            msp_id=msp_id,
            client_id=client.id,
            datasource_id=ds.id,
            is_billing_source=is_billing,
            is_identity_anchor=is_anchor,
            identifier_type=id_type,
            identifier_value=id_value,
            assigned_by=admin_id,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["client_id", "datasource_id"])
        await session.execute(stmt)
    await session.flush()


async def seed_job_runs(
    session: AsyncSession,
    msp_id,
    datasources: dict[str, Datasource],
) -> None:
    count = await session.scalar(
        select(func.count()).select_from(JobRun).where(JobRun.msp_id == msp_id)
    )
    if count and count >= 7:
        return

    now = datetime.now(timezone.utc)
    success_sources = [
        "M365 Production",
        "Proofpoint Core",
        "DropSuite",
        "Datto RMM",
        "SentinelOne",
        "Autotask Billing",
    ]
    runs = []
    runs.append(
        JobRun(
            msp_id=msp_id,
            datasource_id=datasources["Ironscales"].id,
            job_type="SCHEDULED",
            status="FAILED",
            started_at=now - timedelta(hours=4),
            ended_at=now - timedelta(hours=4) + timedelta(seconds=12),
            error_message="API timeout while fetching license usage",
        )
    )
    for i, name in enumerate(success_sources):
        started = now - timedelta(hours=(i + 1) * 6)
        runs.append(
            JobRun(
                msp_id=msp_id,
                datasource_id=datasources[name].id,
                job_type="SCHEDULED",
                status="SUCCESS",
                started_at=started,
                ended_at=started + timedelta(seconds=45 + i * 5),
                records_count=50 + i * 60,
            )
        )
    session.add_all(runs)
    await session.flush()


def _datto_landing_payload() -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "devices": [
            {
                "hostname": "ERES-WS-001",
                "description": "Engineering Laptop - John Smith",
                "serial_number": "SN-ERES-001",
                "company_name": "ERES Companies Inc.",
                "site": "HQ",
                "device_type": "Laptop",
                "last_seen": f"{today}T14:22:00Z",
                "record_date": today,
            },
            {
                "hostname": "ERES-WS-002",
                "description": "Finance Desktop - Jane Doe",
                "serial_number": "SN-ERES-002",
                "company_name": "ERES Companies Inc.",
                "site": "HQ",
                "device_type": "Desktop",
                "last_seen": f"{today}T13:05:00Z",
                "record_date": today,
            },
            {
                "hostname": "SCOOP-LT-101",
                "description": "Sales Laptop - Casey Lee",
                "serial_number": "SN-SCOOP-101",
                "company_name": "Scoop Ride",
                "site": "Remote",
                "device_type": "Laptop",
                "last_seen": f"{today}T09:18:00Z",
                "record_date": today,
            },
            {
                "hostname": "SCOOP-LT-102",
                "description": "Ops Laptop - Rae Patel",
                "serial_number": "SN-SCOOP-102",
                "company_name": "Scoop Ride",
                "site": "Remote",
                "device_type": "Laptop",
                "last_seen": f"{today}T11:42:00Z",
                "record_date": today,
            },
            {
                "hostname": "PINN-WS-201",
                "description": "Partner Workstation - Morgan Hale",
                "serial_number": "SN-PINN-201",
                "company_name": "Pinnacle Legal LLP",
                "site": "Downtown",
                "device_type": "Desktop",
                "last_seen": f"{today}T15:55:00Z",
                "record_date": today,
            },
        ]
    }


def _sentinelone_landing_payload() -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "agents": [
            {
                "agent_id": "s1-agent-001",
                "computer_name": "ERES-WS-001",
                "os": "Windows 11 Pro",
                "tenant_id": "eres-tnt-001",
                "last_active": f"{today}T14:25:00Z",
                "record_date": today,
            },
            {
                "agent_id": "s1-agent-003",
                "computer_name": "ERES-WS-003",
                "os": "Windows 11 Pro",
                "tenant_id": "eres-tnt-001",
                "last_active": f"{today}T10:11:00Z",
                "record_date": today,
            },
            {
                "agent_id": "s1-agent-004",
                "computer_name": "ERES-WS-004",
                "os": "macOS 14",
                "tenant_id": "eres-tnt-001",
                "last_active": f"{today}T12:48:00Z",
                "record_date": today,
            },
            {
                "agent_id": "s1-agent-005",
                "computer_name": "ERES-WS-005",
                "os": "Windows 11 Pro",
                "tenant_id": "eres-tnt-001",
                "last_active": f"{today}T08:30:00Z",
                "record_date": today,
            },
        ]
    }


def _ensure_bucket(s3, bucket: str) -> None:
    """Create the landing bucket if it does not exist (idempotent).

    Guards against the LocalStack bootstrap creating a differently-named bucket
    than the app's configured S3_BUCKET. us-east-1 must not send a
    LocationConstraint; every other region must.
    """
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except ClientError:
        pass
    if settings.AWS_REGION == "us-east-1":
        s3.create_bucket(Bucket=bucket)
    else:
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
        )


def seed_landing_files(msp_id, datasources: dict[str, Datasource]) -> None:
    s3 = localstack_client("s3")
    _ensure_bucket(s3, settings.S3_BUCKET)
    files = [
        (datasources["Datto RMM"].id, _datto_landing_payload()),
        (datasources["SentinelOne"].id, _sentinelone_landing_payload()),
    ]
    for ds_id, payload in files:
        key = _landing_key(msp_id, ds_id)
        try:
            s3.head_object(Bucket=settings.S3_BUCKET, Key=key)
            continue
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey", "NotFound"):
                raise
        s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=json.dumps(payload, indent=2).encode("utf-8"),
            ContentType="application/json",
        )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        msp = await seed_msp(session)
        users = await seed_users(session, msp.id)
        clients = await seed_clients(session, msp.id)
        datasources = await seed_datasources(session, msp.id)
        admin = users["testmsp@mvp.com"]
        await seed_assignments(session, msp.id, admin.id, clients, datasources)
        await seed_job_runs(session, msp.id, datasources)
        await session.commit()

        # Demo landing files are best-effort: a missing/unreachable S3 (LocalStack)
        # must never block the backend from starting. DB seeding above stays strict.
        try:
            seed_landing_files(msp.id, datasources)
        except Exception as exc:  # noqa: BLE001
            print(f"[seed] WARNING: skipped S3 landing-file seed ({type(exc).__name__}): {exc}")

    # seed_connector_registry()
    print("Database seeded successfully")


if __name__ == "__main__":
    asyncio.run(main())
