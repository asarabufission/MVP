from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.login_history import LoginHistory
from app.models.user import User


async def record_login(
    db: AsyncSession,
    *,
    user: User,
    access_token: str,
    refresh_token: str,
    ip: str | None,
    user_agent: str | None,
) -> LoginHistory:
    row = LoginHistory(
        user_id=user.id,
        msp_id=user.msp_id,
        access_token_hash=hash_token(access_token),
        refresh_token_hash=hash_token(refresh_token),
        login_time=datetime.now(timezone.utc),
        ip_address=ip,
        user_agent=user_agent,
        status="ACTIVE",
    )
    db.add(row)
    await db.flush()
    return row


async def find_active_by_refresh_hash(
    db: AsyncSession, refresh_token_hash: str
) -> LoginHistory | None:
    stmt = select(LoginHistory).where(
        LoginHistory.refresh_token_hash == refresh_token_hash,
        LoginHistory.status == "ACTIVE",
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def rotate_tokens(
    db: AsyncSession,
    row: LoginHistory,
    *,
    new_access_hash: str,
    new_refresh_hash: str,
) -> None:
    row.access_token_hash = new_access_hash
    row.refresh_token_hash = new_refresh_hash
    await db.flush()


async def mark_logged_out(db: AsyncSession, *, access_token_hash: str) -> None:
    stmt = select(LoginHistory).where(
        LoginHistory.access_token_hash == access_token_hash,
        LoginHistory.status == "ACTIVE",
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        return
    row.status = "LOGGED_OUT"
    row.logout_time = datetime.now(timezone.utc)
    await db.flush()
