import uuid
from typing import Literal

from app.schemas.common import CamelModel


class LoginRequest(CamelModel):
    username: str
    password: str
    remember_me: bool = False


class RefreshRequest(CamelModel):
    refresh_token: str


class UserPublic(CamelModel):
    id: uuid.UUID
    msp_id: uuid.UUID
    username: str
    email: str
    full_name: str | None = None
    role: Literal["MSP_ADMIN", "MSP_ANALYST"]


class LoginResponse(CamelModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserPublic
    msp_id: uuid.UUID


class MeResponse(UserPublic):
    pass
