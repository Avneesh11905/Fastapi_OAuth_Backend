"""
Module: Tasks
"""
import asyncio
from src.shared.infrastructure.sql.connection import AsyncSessionLocal
from src.shared.adapters.logger import AsyncSQLLogger
from src.authentication.container import get_container

logger = AsyncSQLLogger("BackgroundTasks")
_token_cleanup_task: asyncio.Task | None = None
_user_cleanup_task: asyncio.Task | None = None

async def _periodic_token_cleanup():
    """Background task: clean expired/used refresh tokens every 24h."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                count_tokens = await get_container().refresh_token_repo.cleanup_expired(db)
                if count_tokens:
                    await db.commit()
                    await logger.info(f"Cleaned up {count_tokens} expired/used refresh tokens")
        except asyncio.CancelledError:
            break
        except Exception as e:
            await logger.error(f"Token cleanup task failed: {e}")
        
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            break


async def _periodic_user_cleanup():
    """Background task: clean abandoned unverified users every 24h."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                count_users = await get_container().user_repo.cleanup_unverified_users(db, hours_old=24)
                if count_users:
                    await logger.info(f"Cleaned up {count_users} abandoned unverified user accounts")
                    
                count_soft_deleted = await get_container().user_repo.cleanup_soft_deleted_users(db, days_old=30)
                if count_soft_deleted:
                    await logger.info(f"Permanently purged {count_soft_deleted} soft-deleted user accounts")
                
                if count_users or count_soft_deleted:
                    await db.commit()
        except asyncio.CancelledError:
            break
        except Exception as e:
            await logger.error(f"User cleanup task failed: {e}")
        
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            break


def start_token_cleanup_task():
    global _token_cleanup_task
    if _token_cleanup_task is None:
        _token_cleanup_task = asyncio.create_task(_periodic_token_cleanup())

def stop_token_cleanup_task():
    global _token_cleanup_task
    if _token_cleanup_task is not None:
        _token_cleanup_task.cancel()
        _token_cleanup_task = None

def start_user_cleanup_task():
    global _user_cleanup_task
    if _user_cleanup_task is None:
        _user_cleanup_task = asyncio.create_task(_periodic_user_cleanup())

def stop_user_cleanup_task():
    global _user_cleanup_task
    if _user_cleanup_task is not None:
        _user_cleanup_task.cancel()
        _user_cleanup_task = None
