from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.connector import ConnectorDetailResponse, ConnectorListItem
from app.services.connector_service import get_connector, list_connectors

router = APIRouter()


@router.get("", response_model=list[ConnectorListItem])
async def list_connectors_endpoint(
    user: User = Depends(get_current_user),
) -> list[ConnectorListItem]:
    items = await list_connectors()
    return [
        ConnectorListItem(
            source_id=i["source_id"],
            display_name=i["display_name"],
            category=i["category"],
            source_type=i["source_type"],
            scope_default=i["scope_default"],
            auth_type=i["auth_type"],
            description=i["description"],
        )
        for i in items
    ]


@router.get("/{source_id}", response_model=ConnectorDetailResponse)
async def get_connector_endpoint(
    source_id: str,
    user: User = Depends(get_current_user),
) -> ConnectorDetailResponse:
    bp = await get_connector(source_id)
    return ConnectorDetailResponse(
        source_id=bp["source_id"],
        display_name=bp["display_name"],
        category=bp["category"],
        source_type=bp["source_type"],
        scope_default=bp["scope_default"],
        auth_type=bp["auth_type"],
        description=bp["description"],
        credential_schema=bp["credential_schema"],
        default_field_mappings=bp["default_field_mappings"],
    )
