"""
Shared Infrastructure Container
Instantiates cross-cutting infrastructure adapters exactly once.
"""
from src.shared.config import email_settings
from src.shared.adapters.cache.memory_cache import MemoryCacheAdapter
from src.shared.adapters.task_runner import AsyncioTaskRunner
from src.shared.adapters.email_client import ResendEmailClient
import logging

class SharedContainer:
    def __init__(self):
        # =====================================================================
        # 1. TASK RUNNER
        # =====================================================================
        # To swap to Celery for production, instantiate CeleryTaskRunner() here.
        self.task_runner = AsyncioTaskRunner()
        if isinstance(self.task_runner, AsyncioTaskRunner):
            logging.warning("⚠️  AsyncioTaskRunner is being used. This stores tasks in memory and is NOT recommended for production. See README to swap to CeleryTaskRunner.")

        # =====================================================================
        # 2. CACHE ADAPTER
        # =====================================================================
        # To swap to Redis for production, instantiate RedisCacheAdapter(client=redis_client) here.
        self.cache_adapter = MemoryCacheAdapter()
        if isinstance(self.cache_adapter, MemoryCacheAdapter):
            logging.warning("⚠️  MemoryCacheAdapter is being used. This isolates rate limits per worker and is NOT recommended for production. See README to swap to RedisCacheAdapter.")

        # =====================================================================
        # 3. EMAIL CLIENT
        # =====================================================================
        self.email_client = ResendEmailClient(
            api_key=email_settings.API_KEY,
            from_email=email_settings.FROM,
        )

# Singleton instance
shared_container = SharedContainer()
