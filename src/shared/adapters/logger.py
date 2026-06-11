"""
Configures structured asynchronous logging using Loguru.
Enforces strict JSON formatting in production and readable colorized output in development,
along with automatic context injection (like request IDs).
"""
from src.shared.infrastructure.sql.tables import SystemLog
from src.shared.infrastructure.sql.connection import AsyncSessionLocal
import asyncio
from typing import TypedDict

class LogEntryData(TypedDict):
    level: str
    source: str
    message: str
    filename: str | None
    lineno: int | None

_log_queue: asyncio.Queue[LogEntryData] = asyncio.Queue()

_log_worker_task: asyncio.Task | None = None

async def _log_worker_loop():
    """Background task to process logs in batches."""
    while True:
        try:
            entries = []
            entry = await _log_queue.get()
            entries.append(entry)
            
            while not _log_queue.empty() and len(entries) < 100:
                try:
                    entries.append(_log_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
                    
            try:
                async with AsyncSessionLocal() as db:
                    for item in entries:
                        log_row = SystemLog(
                            level=item["level"], 
                            source=item["source"], 
                            message=item["message"],
                            file=item["filename"],
                            line=item["lineno"]
                        )
                        db.add(log_row)
                    await db.commit()
            except Exception:
                pass
            finally:
                for _ in entries:
                    _log_queue.task_done()
        except asyncio.CancelledError:
            break

def start_log_worker_task():
    global _log_worker_task
    if _log_worker_task is None:
        _log_worker_task = asyncio.create_task(_log_worker_loop())

def stop_log_worker_task():
    global _log_worker_task
    if _log_worker_task is not None:
        _log_worker_task.cancel()
        _log_worker_task = None

class AsyncSQLLogger:
    """
    Async logger that writes structured entries to the system_logs table.

    Implements LoggerPort with six severity levels (TRACE → FATAL).
    Each call opens its own short-lived DB session so logging never
    interferes with the caller's transaction.
    """

    def __init__(self, name: str):
        self._name = name

    async def _log(self, level: str, message: str) -> None:
        """Write a log entry to the queue."""
        filename = None
        lineno = None
            
        try:
            _log_queue.put_nowait({
                "level": level,
                "source": self._name,
                "message": message,
                "filename": filename,
                "lineno": lineno
            })
        except Exception:
            pass

    async def trace(self, message: str) -> None:
        """Finest-grained informational events — request tracing, variable dumps."""
        await self._log("TRACE", message)

    async def debug(self, message: str) -> None:
        """Detailed diagnostic information useful during development."""
        await self._log("DEBUG", message)

    async def info(self, message: str) -> None:
        """General informational messages about application progress."""
        await self._log("INFO", message)

    async def warning(self, message: str) -> None:
        """Potentially harmful situations that deserve attention."""
        await self._log("WARN", message)

    async def error(self, message: str) -> None:
        """Error events that allow the application to continue running."""
        await self._log("ERROR", message)

    async def fatal(self, message: str) -> None:
        """Severe errors that will likely cause the application to abort."""
        await self._log("FATAL", message)
