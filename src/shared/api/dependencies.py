"""
Provides global FastAPI dependencies.
Includes components like the Redis-based rate limiter (SlowAPI), which protects all endpoints from abuse,
and common pagination or sorting extractors used across multiple domains.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.shared.config import database_settings, app_settings

from src.shared.container import shared_container
from src.shared.adapters.cache.memory_cache import MemoryCacheAdapter

storage_uri = "memory://" if isinstance(shared_container.cache_adapter, MemoryCacheAdapter) else database_settings.CACHE_URL

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    enabled=(app_settings.ENV != "development"),
)
