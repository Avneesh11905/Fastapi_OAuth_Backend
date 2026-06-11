"""
Adapter: Redis Cache

Implements CachePort using Redis for production-grade shared caching.
Required when running multiple workers (gunicorn, uvicorn workers) to share
cache state across processes (rate limiting, JWT blacklisting, response caching).
"""
from typing import TYPE_CHECKING, cast
import json

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisCacheAdapter:
    """Implements CachePort using Redis hash sets for structured data caching."""

    def __init__(self, client: "Redis"):
        self._client = client

    async def get_dict(self, key: str) -> dict | None:
        """Retrieve a cached dict by key. Returns None on cache miss."""
        data = await self._client.get(key)
        if not data:
            return None
        return json.loads(data)

    async def set_dict(self, key: str, data: dict, ttl: int) -> None:
        """Store a dict under key using Redis SET with a TTL in seconds."""
        await self._client.set(key, json.dumps(data), ex=ttl)

    async def delete_key(self, key: str) -> None:
        """Remove a key from Redis. No-op if key doesn't exist."""
        await self._client.delete(key)

    async def set_string(self, key: str, value: str, ttl: int) -> None:
        """Store a string with TTL using standard SET."""
        await self._client.set(key, value, ex=ttl)

    async def get_string(self, key: str) -> str | None:
        """Retrieve a string from Redis."""
        return cast(str | None, await self._client.get(key))

    async def incr(self, key: str) -> int:
        return await self._client.incr(key)
