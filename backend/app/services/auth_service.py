from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidCredentialsError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.user import User


async def authenticate(db: AsyncSession, username: str, password: str) -> User:
    stmt = select(User).where(or_(User.email == username, User.username == username))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise InvalidCredentialsError()
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


def issue_token_pair(user: User) -> tuple[str, str, datetime, datetime]:
    access_token, access_exp = create_access_token(
        user_id=user.id, msp_id=user.msp_id, role=user.role
    )
    refresh_token, refresh_exp = create_refresh_token(
        user_id=user.id, msp_id=user.msp_id, role=user.role
    )
    return access_token, refresh_token, access_exp, refresh_exp
