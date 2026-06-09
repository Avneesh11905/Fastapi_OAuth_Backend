"""
Provides global FastAPI dependencies.
Includes components like the Redis-based rate limiter (SlowAPI), which protects all endpoints from abuse,
and common pagination or sorting extractors used across multiple domains.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.shared.config import database_settings, app_settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=database_settings.REDIS_URL,
    enabled=(not app_settings.DEV),
)
