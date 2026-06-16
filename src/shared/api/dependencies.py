"""
Provides global FastAPI dependencies.
Includes components like the Redis-based rate limiter (SlowAPI), which protects all endpoints from abuse,
and common pagination or sorting extractors used across multiple domains.
"""
from slowapi import Limiter
from fastapi import Request
from src.shared.config import database_settings, app_settings

from src.shared.container import shared_container
from src.shared.adapters.cache.memory_cache import MemoryCacheAdapter

storage_uri = "memory://" if isinstance(shared_container.cache_adapter, MemoryCacheAdapter) else database_settings.CACHE_URL

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=storage_uri,
    enabled=(app_settings.ENV != "development"),
)
