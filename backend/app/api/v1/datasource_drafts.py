import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.roles import require_role
from app.models.user import User
from app.schemas.datasource import (
    DraftCreateRequest,
    DraftCreateResponse,
    SchemaPreviewResponse,
    SchemaFieldPreview,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services import datasource_draft_service

router = APIRouter()


@router.post("", response_model=DraftCreateResponse, status_code=201)
async def create_draft_endpoint(
    payload: DraftCreateRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> DraftCreateResponse:
    result = await datasource_draft_service.create_draft(
        db,
        user,
        client_id=payload.client_id,
        blueprint_id=payload.blueprint_id,
        name=payload.name,
        display_name=payload.display_name,
        config=payload.config,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return DraftCreateResponse(**result)


@router.post(
    "/{draft_id}/test-connection",
    response_model=TestConnectionResponse,
)
async def test_connection_endpoint(
    draft_id: uuid.UUID,
    payload: TestConnectionRequest,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    result = await datasource_draft_service.test_connection(
        db,
        user.msp_id,
        draft_id,
        credentials=payload.credentials,
        attempt_id=payload.attempt_id,
    )
    return TestConnectionResponse(
        test_run_id=uuid.UUID(result["test_run_id"]),
        schema_hash=result["schema_hash"],
        fields=[SchemaFieldPreview(**f) for f in result["fields"]],
        sample_rows=result["sample_rows"],
        record_count=result["record_count"],
        column_count=result["column_count"],
        connection_time_ms=result["connection_time_ms"],
        sample_s3_path=result["sample_s3_path"],
        cached=result.get("cached", False),
    )


@router.get(
    "/{draft_id}/schema-preview",
    response_model=SchemaPreviewResponse,
)
async def schema_preview_endpoint(
    draft_id: uuid.UUID,
    user: User = Depends(require_role("MSP_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> SchemaPreviewResponse:
    result = await datasource_draft_service.get_schema_preview(
        db, user.msp_id, draft_id
    )
    return SchemaPreviewResponse(
        fields=[SchemaFieldPreview(**f) for f in result["fields"]],
        schema_hash=result["schema_hash"],
        sample_rows=result["sample_rows"],
        record_count=result["record_count"],
        column_count=result["column_count"],
        expires_at=result.get("expires_at"),
        standard_fields=result["standard_fields"],
    )
