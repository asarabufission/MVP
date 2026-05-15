import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyAssignedError,
    AssignmentInactiveError,
    InvalidBillingSourceError,
    InvalidIdentityAnchorError,
)
from app.models.client import Client
from app.models.client_datasource_assignment import ClientDatasourceAssignment
from app.models.datasource import Datasource
from app.schemas.client import (
    AssignmentCreateRequest,
    ClientAssignmentItem,
)


def _effective(override: str | None, default: str) -> str:
    if override is None or override == "":
        return default
    return override


def _assignment_item(
    *,
    assignment: ClientDatasourceAssignment,
    datasource: Datasource,
    client: Client,
) -> ClientAssignmentItem:
    return ClientAssignmentItem(
        id=assignment.id,
        datasource_id=assignment.datasource_id,
        datasource_name=datasource.name,
        category=datasource.category,
        source_type=datasource.source_type,
        scope=datasource.scope,
        datasource_status=datasource.status,
        is_billing_source=assignment.is_billing_source,
        is_identity_anchor=assignment.is_identity_anchor,
        identifier_type=assignment.identifier_type,
        identifier_value=assignment.identifier_value,
        effective_identifier_type=_effective(
            assignment.identifier_type, client.default_identifier_type
        ),
        effective_identifier_value=_effective(
            assignment.identifier_value, client.default_identifier_value
        ),
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        inactivated_at=assignment.inactivated_at,
    )


async def _load_active_client(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID
) -> Client | None:
    stmt = select(Client).where(
        Client.id == client_id,
        Client.msp_id == msp_id,
        Client.status == "ACTIVE",
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _load_assignment(
    db: AsyncSession,
    msp_id: uuid.UUID,
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> ClientDatasourceAssignment | None:
    stmt = select(ClientDatasourceAssignment).where(
        ClientDatasourceAssignment.client_id == client_id,
        ClientDatasourceAssignment.datasource_id == datasource_id,
        ClientDatasourceAssignment.msp_id == msp_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _load_datasource(
    db: AsyncSession, msp_id: uuid.UUID, datasource_id: uuid.UUID
) -> Datasource | None:
    stmt = select(Datasource).where(
        Datasource.id == datasource_id,
        Datasource.msp_id == msp_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_assignments(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID
) -> list[ClientAssignmentItem] | None:
    client = await _load_active_client(db, msp_id, client_id)
    if client is None:
        return None

    rows = (
        await db.execute(
            select(ClientDatasourceAssignment, Datasource)
            .join(Datasource, Datasource.id == ClientDatasourceAssignment.datasource_id)
            .where(
                ClientDatasourceAssignment.client_id == client_id,
                ClientDatasourceAssignment.msp_id == msp_id,
            )
            .order_by(Datasource.category, Datasource.name)
        )
    ).all()

    return [
        _assignment_item(assignment=a, datasource=d, client=client) for a, d in rows
    ]


async def create_assignment(
    db: AsyncSession,
    msp_id: uuid.UUID,
    admin_id: uuid.UUID,
    client_id: uuid.UUID,
    payload: AssignmentCreateRequest,
) -> ClientAssignmentItem | None:
    client = await _load_active_client(db, msp_id, client_id)
    if client is None:
        return None

    datasource = await _load_datasource(db, msp_id, payload.datasource_id)
    if datasource is None:
        return None
    if datasource.status == "INACTIVE":
        raise AssignmentInactiveError("Cannot assign an INACTIVE datasource")

    existing = await _load_assignment(db, msp_id, client_id, payload.datasource_id)
    if existing is not None and existing.status == "ACTIVE":
        raise AlreadyAssignedError()

    identifier_type = (payload.identifier_type or None) or None
    identifier_value = (payload.identifier_value or None) or None

    if existing is not None and existing.status == "INACTIVE":
        existing.status = "ACTIVE"
        existing.inactivated_at = None
        existing.inactivated_by = None
        existing.identifier_type = identifier_type
        existing.identifier_value = identifier_value
        existing.assigned_by = admin_id
        existing.assigned_at = datetime.now(timezone.utc)
        assignment = existing
    else:
        assignment = ClientDatasourceAssignment(
            msp_id=msp_id,
            client_id=client_id,
            datasource_id=payload.datasource_id,
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            assigned_by=admin_id,
        )
        db.add(assignment)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AlreadyAssignedError() from exc

    await recompute_readiness(db, msp_id, client_id)
    await db.flush()

    return _assignment_item(assignment=assignment, datasource=datasource, client=client)


async def inactivate_assignment(
    db: AsyncSession,
    msp_id: uuid.UUID,
    admin_id: uuid.UUID,
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> ClientAssignmentItem | None:
    client = await _load_active_client(db, msp_id, client_id)
    if client is None:
        return None

    assignment = await _load_assignment(db, msp_id, client_id, datasource_id)
    if assignment is None:
        return None

    if assignment.status == "ACTIVE":
        assignment.status = "INACTIVE"
        assignment.inactivated_at = datetime.now(timezone.utc)
        assignment.inactivated_by = admin_id
        # Clearing flags is required by the partial unique indexes
        # (ux_client_billing_source / ux_client_identity_anchor exist only
        # WHERE status='ACTIVE', but clearing keeps the row semantically clean).
        assignment.is_billing_source = False
        assignment.is_identity_anchor = False
        await db.flush()
        await recompute_readiness(db, msp_id, client_id)
        await db.flush()

    datasource = await _load_datasource(db, msp_id, datasource_id)
    assert datasource is not None
    return _assignment_item(assignment=assignment, datasource=datasource, client=client)


async def reactivate_assignment(
    db: AsyncSession,
    msp_id: uuid.UUID,
    admin_id: uuid.UUID,
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> ClientAssignmentItem | None:
    client = await _load_active_client(db, msp_id, client_id)
    if client is None:
        return None

    assignment = await _load_assignment(db, msp_id, client_id, datasource_id)
    if assignment is None:
        return None

    datasource = await _load_datasource(db, msp_id, datasource_id)
    if datasource is None:
        return None
    if datasource.status == "INACTIVE":
        raise AssignmentInactiveError("Cannot reactivate against an INACTIVE datasource")

    if assignment.status == "INACTIVE":
        assignment.status = "ACTIVE"
        assignment.inactivated_at = None
        assignment.inactivated_by = None
        assignment.assigned_by = admin_id
        await db.flush()
        await recompute_readiness(db, msp_id, client_id)
        await db.flush()

    return _assignment_item(assignment=assignment, datasource=datasource, client=client)


async def set_billing_source(
    db: AsyncSession,
    msp_id: uuid.UUID,
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> ClientAssignmentItem | None:
    client = await _load_active_client(db, msp_id, client_id)
    if client is None:
        return None

    assignment = await _load_assignment(db, msp_id, client_id, datasource_id)
    if assignment is None:
        return None
    if assignment.status != "ACTIVE":
        raise AssignmentInactiveError()

    datasource = await _load_datasource(db, msp_id, datasource_id)
    assert datasource is not None
    if datasource.category != "RECONCILIATION":
        raise InvalidBillingSourceError()

    await db.execute(
        update(ClientDatasourceAssignment)
        .where(
            ClientDatasourceAssignment.client_id == client_id,
            ClientDatasourceAssignment.msp_id == msp_id,
            ClientDatasourceAssignment.id != assignment.id,
            ClientDatasourceAssignment.is_billing_source.is_(True),
        )
        .values(is_billing_source=False)
    )
    assignment.is_billing_source = True
    await db.flush()
    await recompute_readiness(db, msp_id, client_id)
    await db.flush()

    return _assignment_item(assignment=assignment, datasource=datasource, client=client)


async def set_identity_anchor(
    db: AsyncSession,
    msp_id: uuid.UUID,
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
) -> ClientAssignmentItem | None:
    client = await _load_active_client(db, msp_id, client_id)
    if client is None:
        return None

    assignment = await _load_assignment(db, msp_id, client_id, datasource_id)
    if assignment is None:
        return None
    if assignment.status != "ACTIVE":
        raise AssignmentInactiveError()

    datasource = await _load_datasource(db, msp_id, datasource_id)
    assert datasource is not None
    if datasource.category != "LICENSING":
        raise InvalidIdentityAnchorError()

    await db.execute(
        update(ClientDatasourceAssignment)
        .where(
            ClientDatasourceAssignment.client_id == client_id,
            ClientDatasourceAssignment.msp_id == msp_id,
            ClientDatasourceAssignment.id != assignment.id,
            ClientDatasourceAssignment.is_identity_anchor.is_(True),
        )
        .values(is_identity_anchor=False)
    )
    assignment.is_identity_anchor = True
    await db.flush()
    await recompute_readiness(db, msp_id, client_id)
    await db.flush()

    return _assignment_item(assignment=assignment, datasource=datasource, client=client)


async def recompute_readiness(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID
) -> None:
    """READY iff ACTIVE assignments contain >=1 LICENSING + >=1 ENDPOINT + a
    billing source + an identity anchor + at least one referenced datasource
    has had a successful run (last_run_at is set) + no referenced datasource
    is DEGRADED. DEGRADED if any referenced ACTIVE datasource is DEGRADED.
    Otherwise NEEDS_SETUP."""
    rows = (
        await db.execute(
            select(
                Datasource.category,
                Datasource.status.label("ds_status"),
                Datasource.last_run_at,
                ClientDatasourceAssignment.is_billing_source,
                ClientDatasourceAssignment.is_identity_anchor,
            )
            .join(Datasource, Datasource.id == ClientDatasourceAssignment.datasource_id)
            .where(
                ClientDatasourceAssignment.client_id == client_id,
                ClientDatasourceAssignment.msp_id == msp_id,
                ClientDatasourceAssignment.status == "ACTIVE",
            )
        )
    ).all()

    has_licensing = any(r.category == "LICENSING" for r in rows)
    has_endpoint = any(r.category == "ENDPOINT" for r in rows)
    has_billing = any(r.is_billing_source for r in rows)
    has_anchor = any(r.is_identity_anchor for r in rows)
    has_run = any(r.last_run_at is not None for r in rows)
    has_degraded = any(r.ds_status == "DEGRADED" for r in rows)

    if has_degraded:
        readiness = "DEGRADED"
    elif (
        has_licensing
        and has_endpoint
        and has_billing
        and has_anchor
        and has_run
    ):
        readiness = "READY"
    else:
        readiness = "NEEDS_SETUP"

    await db.execute(
        update(Client)
        .where(Client.id == client_id, Client.msp_id == msp_id)
        .values(readiness=readiness)
    )
