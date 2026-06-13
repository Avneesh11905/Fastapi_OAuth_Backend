"""
Exposes liveness and readiness probes for orchestrators (like Kubernetes or Docker Compose).
Checks connectivity to the PostgreSQL database and Redis cache to ensure the application is healthy.
"""
from fastapi import APIRouter, Depends
from typing import Annotated
from src.shared.infrastructure.sql.uow import SQLAlchemyUnitOfWork, get_uow
from sqlalchemy import text
from fastapi.responses import JSONResponse
from src.shared.config import database_settings

router = APIRouter()




@router.get("/health")
async def health_check(uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)]):
    # Check DB
    try:
        await uow.session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
        
    # Check Redis/Cache
    from src.shared.container import shared_container
    from src.shared.adapters.cache.memory_cache import MemoryCacheAdapter
    
    cache_status = "ok"
    if not isinstance(shared_container.cache_adapter, MemoryCacheAdapter):
        if database_settings.CACHE_URL.startswith("redis"):
            try:
                import redis.asyncio as redis
                client = redis.from_url(database_settings.CACHE_URL)
                await client.ping()
                cache_status = "ok"
            except Exception:
                cache_status = "error"
        
    status_str = "ok" if db_status == "ok" and cache_status == "ok" else "degraded"
    return JSONResponse(
        status_code=200 if status_str == "ok" else 503,
        content={
            "status": status_str,
            "database": db_status,
            "cache": cache_status
        }
    )
