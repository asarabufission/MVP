import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TokenExpiredError
from app.core.security import TokenExpired, TokenInvalid, decode_token, hash_token
from app.db.session import get_db
from app.models.user import User

__all__ = ["get_db", "get_current_user", "oauth2_scheme"]

oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise TokenExpiredError()

    token = creds.credentials
    try:
        payload = decode_token(token, expected_type="access")
    except (TokenExpired, TokenInvalid) as exc:
        raise TokenExpiredError() from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise TokenExpiredError() from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise TokenExpiredError()

    request.state.access_token_hash = hash_token(token)
    return user
