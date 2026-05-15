import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.roles import require_role
from app.models.user import User
from app.schemas.client import (
    AssignmentCreateRequest,
    ClientAssignmentItem,
    IdentifierOverrideRequest,
)
from app.services.client_assignment_service import (
    create_assignment,
    inactivate_assignment,
    list_assignments,
    reactivate_assignment,
    set_billing_source,
    set_identity_anchor,
)
from app.services.client_service import set_assignment_identifier

router = APIRouter()


@router.get(
    "/{client_id}/assignments",
    response_model=list[ClientAssignmentItem],
)
async def list_assignments_endpoint(
    client_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClientAssignmentItem]:
    items = await list_assignments(db, user.msp_id, client_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return items


@router.post(
    "/{client_id}/assignments",
    response_model=ClientAssignmentItem,
    status_code=201,
)
async def create_assignment_endpoint(
    client_id: uuid.UUID,
    payload: AssignmentCreateRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientAssignmentItem:
    item = await create_assignment(db, user.msp_id, user.id, client_id, payload)
    if item is None:
        raise HTTPException(status_code=404, detail="Client or datasource not found")
    return item


@router.post(
    "/{client_id}/assignments/{datasource_id}/inactivate",
    response_model=ClientAssignmentItem,
)
async def inactivate_assignment_endpoint(
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientAssignmentItem:
    item = await inactivate_assignment(
        db, user.msp_id, user.id, client_id, datasource_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return item


@router.post(
    "/{client_id}/assignments/{datasource_id}/reactivate",
    response_model=ClientAssignmentItem,
)
async def reactivate_assignment_endpoint(
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientAssignmentItem:
    item = await reactivate_assignment(
        db, user.msp_id, user.id, client_id, datasource_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return item


@router.post(
    "/{client_id}/assignments/{datasource_id}/set-billing-source",
    response_model=ClientAssignmentItem,
)
async def set_billing_source_endpoint(
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientAssignmentItem:
    item = await set_billing_source(db, user.msp_id, client_id, datasource_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return item


@router.post(
    "/{client_id}/assignments/{datasource_id}/set-identity-anchor",
    response_model=ClientAssignmentItem,
)
async def set_identity_anchor_endpoint(
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientAssignmentItem:
    item = await set_identity_anchor(db, user.msp_id, client_id, datasource_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return item


@router.patch(
    "/{client_id}/assignments/{datasource_id}/identifier",
    response_model=ClientAssignmentItem,
)
async def set_assignment_identifier_endpoint(
    client_id: uuid.UUID,
    datasource_id: uuid.UUID,
    payload: IdentifierOverrideRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientAssignmentItem:
    item = await set_assignment_identifier(
        db, user.msp_id, client_id, datasource_id, payload
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return item
