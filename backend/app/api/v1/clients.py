import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.roles import require_role
from app.models.user import User
from app.schemas.client import (
    ClientCreateRequest,
    ClientDetailResponse,
    ClientListResponse,
    ClientPatchRequest,
)
from app.services.client_service import (
    create_client,
    get_client_detail,
    list_clients,
    patch_client,
    soft_delete_client,
)

router = APIRouter()


@router.get("", response_model=ClientListResponse)
async def list_clients_endpoint(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientListResponse:
    return await list_clients(
        db, user.msp_id, search=search, limit=limit, cursor=cursor
    )


@router.post("", response_model=ClientDetailResponse, status_code=201)
async def create_client_endpoint(
    payload: ClientCreateRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientDetailResponse:
    row = await create_client(db, user.msp_id, payload)
    detail = await get_client_detail(db, user.msp_id, row.id)
    assert detail is not None
    return detail


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client_endpoint(
    client_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientDetailResponse:
    detail = await get_client_detail(db, user.msp_id, client_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return detail


@router.patch("/{client_id}", response_model=ClientDetailResponse)
async def patch_client_endpoint(
    client_id: uuid.UUID,
    payload: ClientPatchRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> ClientDetailResponse:
    row = await patch_client(db, user.msp_id, client_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Client not found")
    detail = await get_client_detail(db, user.msp_id, row.id)
    assert detail is not None
    return detail


@router.delete("/{client_id}", status_code=204)
async def delete_client_endpoint(
    client_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    deleted = await soft_delete_client(db, user.msp_id, client_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    return Response(status_code=204)
