"""
Adapter: Memory Cache

Implements CachePort using an in-memory dictionary for local development.
No external dependencies needed — works out of the box.

WARNING: Do NOT use in production with multiple workers. Each worker gets
an isolated in-memory store which breaks rate limiting and JWT blacklisting.
See README Section 12.1 for details.
"""
import json
import time
import asyncio


class MemoryCacheAdapter:
    """Implements CachePort using a thread-safe in-memory dictionary."""

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

    async def incr(self, key: str, ttl: int | None = None) -> int:
        async with self._lock:
            self._cleanup()
            item = self._store.get(key)
            val, expire_at = 0, time.time() + (ttl if ttl is not None else 31_536_000)  # 1-year "never expire" sentinel
            if item:
                try:
                    val = int(item[0])
                except ValueError:
                    val = 0
                expire_at = item[1]  # preserve existing TTL on subsequent calls
            val += 1
            self._store[key] = (str(val), expire_at)
            return val
