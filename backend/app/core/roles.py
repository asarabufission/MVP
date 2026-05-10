from typing import Awaitable, Callable

from fastapi import Depends

from app.api.deps import get_current_user
from app.core.exceptions import RoleForbiddenError
from app.models.user import User


def require_role(*roles: str) -> Callable[..., Awaitable[User]]:
    allowed = set(roles)

    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise RoleForbiddenError()
        return user

    return _dependency
