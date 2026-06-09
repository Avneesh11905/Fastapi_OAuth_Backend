"""
Manages the global Redis connection pool.
Instantiates an asynchronous Redis client used for caching, rate limiting, and token blacklisting.
"""
from redis.asyncio import Redis
from src.shared.config import database_settings

redis_client = Redis(
    host=database_settings.REDIS_HOST,
    port=database_settings.REDIS_PORT,
    db=database_settings.REDIS_DB,
    username=database_settings.REDIS_USERNAME,
    password=database_settings.REDIS_PASSWORD,
    decode_responses=True
)
