"""
Port: Cache

Defines the generic interface for a key-value cache with TTL support.
Any domain can depend on this port. Infrastructure adapters (Redis, Memcached, Memory)
live in src/shared/adapters/.
"""
from typing import Protocol


class CachePort(Protocol):
    """Interface for a generic key-value cache with TTL support."""

    async def get_dict(self, key: str) -> dict | None:
        """Retrieve a cached dict by key. Returns None on cache miss."""
        ...

    async def set_dict(self, key: str, data: dict, ttl: int) -> None:
        """Store a dict under key with a TTL in seconds."""
        ...

    async def delete_key(self, key: str) -> None:
        """Remove a key from the cache. No-op if key doesn't exist."""
        ...

    async def set_string(self, key: str, value: str, ttl: int) -> None:
        """Store a string value with TTL."""
        ...

    async def get_string(self, key: str) -> str | None:
        """Retrieve a string value."""
        ...

    async def incr(self, key: str, ttl: int | None = None) -> int:
        """Atomically increment a key and return the new value. If ttl is given, sets expiry on first creation only (NX)."""
        ...
