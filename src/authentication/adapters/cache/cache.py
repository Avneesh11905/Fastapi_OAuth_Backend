"""
Cache Adapters

This module contains implementations for the CachePort.
- RedisCacheAdapter: High-performance, ephemeral storage using Redis for production.
- MemoryCacheAdapter: In-memory dictionary cache for local development without Redis.
"""
from typing import TYPE_CHECKING, cast
import json
import time
import asyncio

if TYPE_CHECKING:
    from redis.asyncio import Redis

class RedisCacheAdapter:
    """Implements CachePort using Redis hash sets for structured data caching."""

    def __init__(self, client: "Redis"):
        self._client = client

    async def get_dict(self, key: str) -> dict | None:
        """Retrieve a cached dict by key. Returns None on cache miss."""
        data = await self._client.hgetall(key)
        if not data:
            return None
            
        return data

    async def set_dict(self, key: str, data: dict, ttl: int) -> None:
        """Store a dict under key using Redis HSET with a TTL in seconds."""
        await self._client.hset(key, mapping=data)
        await self._client.expire(key, ttl)

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


class MemoryCacheAdapter:
    """Implements CachePort using an in-memory dictionary."""
    
    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    def _cleanup(self):
        """Removes expired keys from the store."""
        now = time.time()
        expired = [k for k, v in self._store.items() if v[1] < now]
        for k in expired:
            del self._store[k]

    async def get_dict(self, key: str) -> dict | None:
        async with self._lock:
            self._cleanup()
            item = self._store.get(key)
            if item:
                return json.loads(item[0])
            return None

    async def set_dict(self, key: str, data: dict, ttl: int) -> None:
        async with self._lock:
            self._cleanup()
            expire_at = time.time() + ttl
            self._store[key] = (json.dumps(data), expire_at)


    async def delete_key(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    
    async def set_string(self, key: str, value: str, ttl: int) -> None:
        async with self._lock:
            self._cleanup()
            expire_at = time.time() + ttl
            self._store[key] = (value, expire_at)

    async def get_string(self, key: str) -> str | None:
        async with self._lock:
            self._cleanup()
            item = self._store.get(key)
            if item:
                return item[0]
            return None

    async def incr(self, key: str) -> int:
        async with self._lock:
            self._cleanup()
            item = self._store.get(key)
            val = 0
            expire_at = time.time() + 31536000 # 1 year default
            if item:
                try:
                    val = int(item[0])
                except ValueError:
                    val = 0
                expire_at = item[1]
            val += 1
            self._store[key] = (str(val), expire_at)
            return val
