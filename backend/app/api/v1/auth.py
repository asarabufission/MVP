import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import InvalidRefreshTokenError
from app.core.roles import require_role
from app.core.security import (
    TokenExpired,
    TokenInvalid,
    access_token_expires_in_seconds,
    decode_token,
    hash_token,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    UserPublic,
)
from app.services.auth_service import authenticate, issue_token_pair
from app.services.login_history_service import (
    find_active_by_refresh_hash,
    mark_logged_out,
    record_login,
    rotate_tokens,
)

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _build_login_response(
    user: User, access_token: str, refresh_token: str
) -> LoginResponse:
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_token_expires_in_seconds(),
        user=UserPublic.model_validate(user),
        msp_id=user.msp_id,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    user = await authenticate(db, payload.username, payload.password)
    access_token, refresh_token, _, _ = issue_token_pair(user)
    await record_login(
        db,
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return _build_login_response(user, access_token, refresh_token)


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
    except (TokenExpired, TokenInvalid) as exc:
        raise InvalidRefreshTokenError() from exc

    refresh_hash = hash_token(payload.refresh_token)
    row = await find_active_by_refresh_hash(db, refresh_hash)
    if row is None:
        raise InvalidRefreshTokenError()

    try:
        sub_uuid = uuid.UUID(decoded["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidRefreshTokenError() from exc

    if row.user_id != sub_uuid:
        raise InvalidRefreshTokenError()

    result = await db.execute(select(User).where(User.id == row.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise InvalidRefreshTokenError()

    new_access, new_refresh, _, _ = issue_token_pair(user)
    await rotate_tokens(
        db,
        row,
        new_access_hash=hash_token(new_access),
        new_refresh_hash=hash_token(new_refresh),
    )
    return _build_login_response(user, new_access, new_refresh)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    access_token_hash = getattr(request.state, "access_token_hash", None)
    if access_token_hash:
        await mark_logged_out(db, access_token_hash=access_token_hash)
    return Response(status_code=204)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse.model_validate(user)


@router.get("/_probe-admin")
async def probe_admin(_: User = Depends(require_role("MSP_ADMIN"))) -> dict[str, bool]:
    return {"ok": True}


@router.get("/_probe-any")
async def probe_any(_: User = Depends(get_current_user)) -> dict[str, bool]:
    return {"ok": True}
