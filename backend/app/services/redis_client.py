import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

_pool: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _pool


async def cache_get(key: str) -> dict[str, Any] | None:
    client = get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    client = get_redis()
    await client.set(key, json.dumps(value), ex=ttl_seconds)
