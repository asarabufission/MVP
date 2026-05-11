import base64
import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AssignmentInactiveError,
    ClientNameTakenError,
    InvalidCursorError,
    InvalidIdentifierError,
)
from app.models.client import Client
from app.models.client_datasource_assignment import ClientDatasourceAssignment
from app.models.datasource import Datasource
from app.schemas.client import (
    ClientAssignmentItem,
    ClientCreateRequest,
    ClientDetailResponse,
    ClientListItem,
    ClientListResponse,
    ClientPatchRequest,
    IdentifierOverrideRequest,
)


def _encode_cursor(created_at: datetime, row_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{row_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        pad = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + pad).decode()
        ts_iso, id_str = raw.split("|", 1)
        return datetime.fromisoformat(ts_iso), uuid.UUID(id_str)
    except Exception as exc:  # noqa: BLE001
        raise InvalidCursorError() from exc


def _effective(
    override: str | None, default: str
) -> str:
    if override is None or override == "":
        return default
    return override


async def _aggregate_assignments(
    db: AsyncSession, client_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict[str, object]]:
    """Compute (assigned_count, billing_source_name, identity_anchor_name)
    per client_id from ACTIVE assignments only."""
    if not client_ids:
        return {}
    rows = (
        await db.execute(
            select(
                ClientDatasourceAssignment.client_id,
                ClientDatasourceAssignment.is_billing_source,
                ClientDatasourceAssignment.is_identity_anchor,
                Datasource.name.label("datasource_name"),
            )
            .join(Datasource, Datasource.id == ClientDatasourceAssignment.datasource_id)
            .where(
                ClientDatasourceAssignment.client_id.in_(client_ids),
                ClientDatasourceAssignment.status == "ACTIVE",
            )
        )
    ).all()

    out: dict[uuid.UUID, dict[str, object]] = {
        cid: {"assigned_count": 0, "billing_source_name": None, "identity_anchor_name": None}
        for cid in client_ids
    }
    for r in rows:
        slot = out[r.client_id]
        slot["assigned_count"] = (slot["assigned_count"] or 0) + 1  # type: ignore[operator]
        if r.is_billing_source:
            slot["billing_source_name"] = r.datasource_name
        if r.is_identity_anchor:
            slot["identity_anchor_name"] = r.datasource_name
    return out


async def list_clients(
    db: AsyncSession,
    msp_id: uuid.UUID,
    *,
    search: str | None,
    limit: int,
    cursor: str | None,
) -> ClientListResponse:
    base_filters = [Client.msp_id == msp_id, Client.status == "ACTIVE"]
    if search:
        base_filters.append(Client.name.ilike(f"%{search}%"))

    total_count = await db.scalar(
        select(func.count()).select_from(Client).where(and_(*base_filters))
    ) or 0

    page_filters = list(base_filters)
    if cursor:
        c_ts, c_id = _decode_cursor(cursor)
        page_filters.append(
            tuple_(Client.created_at, Client.id) < tuple_(c_ts, c_id)
        )

    rows = (
        await db.execute(
            select(Client)
            .where(and_(*page_filters))
            .order_by(Client.created_at.desc(), Client.id.desc())
            .limit(limit + 1)
        )
    ).scalars().all()

    next_cursor: str | None = None
    if len(rows) > limit:
        rows = list(rows[:limit])
        last = rows[-1]
        next_cursor = _encode_cursor(last.created_at, last.id)

    aggregates = await _aggregate_assignments(db, [r.id for r in rows])

    items = [
        ClientListItem(
            id=r.id,
            name=r.name,
            description=r.description,
            default_identifier_type=r.default_identifier_type,
            default_identifier_value=r.default_identifier_value,
            readiness=r.readiness,
            assigned_count=int(aggregates.get(r.id, {}).get("assigned_count", 0) or 0),
            billing_source_name=aggregates.get(r.id, {}).get("billing_source_name"),  # type: ignore[arg-type]
            identity_anchor_name=aggregates.get(r.id, {}).get("identity_anchor_name"),  # type: ignore[arg-type]
            created_at=r.created_at,
        )
        for r in rows
    ]

    return ClientListResponse(
        items=items, next_cursor=next_cursor, total_count=int(total_count)
    )


async def _load_client(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID, *, allow_inactive: bool = False
) -> Client | None:
    stmt = select(Client).where(Client.id == client_id, Client.msp_id == msp_id)
    if not allow_inactive:
        stmt = stmt.where(Client.status == "ACTIVE")
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_client_detail(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID
) -> ClientDetailResponse | None:
    client = await _load_client(db, msp_id, client_id)
    if client is None:
        return None

    assignment_rows = (
        await db.execute(
            select(
                ClientDatasourceAssignment.id,
                ClientDatasourceAssignment.datasource_id,
                ClientDatasourceAssignment.is_billing_source,
                ClientDatasourceAssignment.is_identity_anchor,
                ClientDatasourceAssignment.identifier_type,
                ClientDatasourceAssignment.identifier_value,
                ClientDatasourceAssignment.status,
                ClientDatasourceAssignment.assigned_at,
                ClientDatasourceAssignment.inactivated_at,
                Datasource.name.label("datasource_name"),
                Datasource.category,
                Datasource.source_type,
                Datasource.scope,
                Datasource.status.label("datasource_status"),
            )
            .join(Datasource, Datasource.id == ClientDatasourceAssignment.datasource_id)
            .where(ClientDatasourceAssignment.client_id == client.id)
            .order_by(Datasource.category, Datasource.name)
        )
    ).all()

    assignments = [
        ClientAssignmentItem(
            id=row.id,
            datasource_id=row.datasource_id,
            datasource_name=row.datasource_name,
            category=row.category,
            source_type=row.source_type,
            scope=row.scope,
            datasource_status=row.datasource_status,
            is_billing_source=row.is_billing_source,
            is_identity_anchor=row.is_identity_anchor,
            identifier_type=row.identifier_type,
            identifier_value=row.identifier_value,
            effective_identifier_type=_effective(
                row.identifier_type, client.default_identifier_type
            ),
            effective_identifier_value=_effective(
                row.identifier_value, client.default_identifier_value
            ),
            status=row.status,
            assigned_at=row.assigned_at,
            inactivated_at=row.inactivated_at,
        )
        for row in assignment_rows
    ]

    active_assignments = [a for a in assignments if a.status == "ACTIVE"]
    billing = next((a for a in active_assignments if a.is_billing_source), None)
    anchor = next((a for a in active_assignments if a.is_identity_anchor), None)

    return ClientDetailResponse(
        id=client.id,
        name=client.name,
        description=client.description,
        default_identifier_type=client.default_identifier_type,
        default_identifier_value=client.default_identifier_value,
        readiness=client.readiness,
        assigned_count=len(active_assignments),
        billing_source_name=billing.datasource_name if billing else None,
        identity_anchor_name=anchor.datasource_name if anchor else None,
        created_at=client.created_at,
        updated_at=client.updated_at,
        assignments=assignments,
    )


async def create_client(
    db: AsyncSession, msp_id: uuid.UUID, payload: ClientCreateRequest
) -> Client:
    row = Client(
        msp_id=msp_id,
        name=payload.name,
        description=payload.description,
        default_identifier_type=payload.default_identifier_type,
        default_identifier_value=payload.default_identifier_value,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ClientNameTakenError() from exc
    await db.refresh(row)
    return row


async def patch_client(
    db: AsyncSession,
    msp_id: uuid.UUID,
    client_id: uuid.UUID,
    payload: ClientPatchRequest,
) -> Client | None:
    client = await _load_client(db, msp_id, client_id)
    if client is None:
        return None

    data = payload.model_dump(exclude_unset=True, by_alias=False)
    for field, value in data.items():
        setattr(client, field, value)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ClientNameTakenError() from exc
    await db.refresh(client)
    return client


async def soft_delete_client(
    db: AsyncSession, msp_id: uuid.UUID, client_id: uuid.UUID
) -> bool:
    client = await _load_client(db, msp_id, client_id, allow_inactive=True)
    if client is None:
        return False
    client.status = "INACTIVE"
    await db.flush()
    return True


async def set_assignment_identifier(
    db: AsyncSession,
    msp_id: uuid.UUID,
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
    payload: IdentifierOverrideRequest,
) -> ClientAssignmentItem | None:
    client = await _load_client(db, msp_id, client_id)
    if client is None:
        return None

    assignment = (
        await db.execute(
            select(ClientDatasourceAssignment).where(
                ClientDatasourceAssignment.client_id == client_id,
                ClientDatasourceAssignment.datasource_id == datasource_id,
                ClientDatasourceAssignment.msp_id == msp_id,
            )
        )
    ).scalar_one_or_none()

    if assignment is None:
        return None

    if assignment.status == "INACTIVE":
        raise AssignmentInactiveError()

    t = payload.identifier_type
    v = payload.identifier_value
    if t == "" and v == "":
        assignment.identifier_type = None
        assignment.identifier_value = None
    elif t and v:
        assignment.identifier_type = t
        assignment.identifier_value = v
    else:
        raise InvalidIdentifierError(
            "Both identifierType and identifierValue must be provided, or both empty to clear."
        )

    await db.flush()

    ds = (
        await db.execute(select(Datasource).where(Datasource.id == datasource_id))
    ).scalar_one()

    return ClientAssignmentItem(
        id=assignment.id,
        datasource_id=assignment.datasource_id,
        datasource_name=ds.name,
        category=ds.category,
        source_type=ds.source_type,
        scope=ds.scope,
        datasource_status=ds.status,
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
