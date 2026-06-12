from celery import Celery # type: ignore
import os

redis_url = os.environ.get("CACHE_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "auth_tasks",
    broker=redis_url,
    backend=redis_url
)
