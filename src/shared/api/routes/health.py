"""
Exposes liveness and readiness probes for orchestrators (like Kubernetes or Docker Compose).
Checks connectivity to the PostgreSQL database and Redis cache to ensure the application is healthy.
"""
from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.sql.connection import get_db
from sqlalchemy import text
from fastapi.responses import JSONResponse
from src.shared.config import app_settings, database_settings

router = APIRouter()




@router.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
        
    # Check Redis/Cache
    cache_status = "ok"
    if not app_settings.USE_MEMORY_CACHE:
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
