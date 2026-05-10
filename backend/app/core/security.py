import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def access_token_expires_in_seconds() -> int:
    return settings.ACCESS_TOKEN_TTL_MINUTES * 60


def _build_payload(
    *,
    user_id: uuid.UUID,
    msp_id: uuid.UUID,
    role: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[dict[str, Any], datetime]:
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    payload = {
        "sub": str(user_id),
        "msp_id": str(msp_id),
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return payload, exp


def create_access_token(
    *, user_id: uuid.UUID, msp_id: uuid.UUID, role: str
) -> tuple[str, datetime]:
    payload, exp = _build_payload(
        user_id=user_id,
        msp_id=msp_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES),
    )
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, exp


def create_refresh_token(
    *, user_id: uuid.UUID, msp_id: uuid.UUID, role: str
) -> tuple[str, datetime]:
    payload, exp = _build_payload(
        user_id=user_id,
        msp_id=msp_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
    )
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, exp


class TokenExpired(Exception):
    pass


class TokenInvalid(Exception):
    pass


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except JWTError as exc:
        raise TokenInvalid() from exc

    if payload.get("type") != expected_type:
        raise TokenInvalid()
    return payload
