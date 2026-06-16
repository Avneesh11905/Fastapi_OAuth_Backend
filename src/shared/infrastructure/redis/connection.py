"""
Manages the global Redis connection pool.
Instantiates an asynchronous Redis client used for caching, rate limiting, and token blacklisting.
"""
from redis.asyncio import Redis

from src.shared.config import database_settings

redis_client = Redis.from_url(
    database_settings.CACHE_URL,
    decode_responses=True
)
