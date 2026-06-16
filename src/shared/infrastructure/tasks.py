"""
Provides a generic interface for executing background tasks.
Wraps `asyncio.create_task` or a message broker client to ensure "fire-and-forget" operations
(like sending emails) don't block the HTTP response.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from src.shared.adapters.logger import AsyncSQLLogger
from src.shared.config import log_settings
from src.shared.infrastructure.sql.connection import AsyncSessionLocal
from src.shared.infrastructure.sql.tables import SystemLog

logger = AsyncSQLLogger("LogCleanupTask")
_cleanup_task: asyncio.Task | None = None

async def _periodic_log_cleanup():
    """Background task: clean old logs."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=log_settings.RETENTION_DAYS)
                result = await db.execute(delete(SystemLog).where(SystemLog.created_at < cutoff_date))
                await db.commit()
                rowcount = getattr(result, "rowcount", 0)
                if rowcount > 0:
                    await logger.info(f"Cleaned up {rowcount} old logs")
        except asyncio.CancelledError:
            break
        except Exception as e:
            await logger.error(f"Log cleanup failed: {e}")
        
        # Sleep for 24 hours
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            break

def start_log_cleanup_task():
    """Starts the periodic background task for log cleanup."""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(_periodic_log_cleanup())

def stop_log_cleanup_task():
    """Stops the periodic background task for log cleanup."""
    global _cleanup_task
    if _cleanup_task is not None:
        _cleanup_task.cancel()
        _cleanup_task = None
