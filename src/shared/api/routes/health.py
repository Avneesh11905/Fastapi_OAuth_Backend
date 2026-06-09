"""
Exposes liveness and readiness probes for orchestrators (like Kubernetes or Docker Compose).
Checks connectivity to the PostgreSQL database and Redis cache to ensure the application is healthy.
"""
from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.sql.connection import get_db
from sqlalchemy import text
from src.authentication.api.container import get_container

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
    cache = get_container().cache_adapter
    try:
        await cache.set_string("health_ping", "pong", 5)
        val = await cache.get_string("health_ping")
        cache_status = "ok" if val == "pong" else "error"
    except Exception:
        cache_status = "error"
        
    return {
        "status": "ok" if db_status == "ok" and cache_status == "ok" else "degraded",
        "database": db_status,
        "cache": cache_status
    }
