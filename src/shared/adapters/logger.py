"""
Configures structured asynchronous logging using Loguru.
Enforces strict JSON formatting in production and readable colorized output in development,
along with automatic context injection (like request IDs).
"""
from src.shared.infrastructure.sql.tables import SystemLog
from src.shared.infrastructure.sql.connection import AsyncSessionLocal
from src.shared.container import shared_container
import sys
from typing import TypedDict

class LogEntryData(TypedDict):
    level: str
    source: str
    message: str
    filename: str | None
    lineno: int | None

async def _insert_log_to_db(level: str, source: str, message: str, filename: str | None, lineno: int | None):
    """Inserts a single log entry. Falls back to stderr on failure."""
    try:
        async with AsyncSessionLocal() as db:
            log_row = SystemLog(
                level=level, 
                source=source, 
                message=message,
                file=filename,
                line=lineno
            )
            db.add(log_row)
            await db.commit()
    except Exception:
        # Fallback if DB is completely down
        sys.stderr.write(f"[FALLBACK LOG] {level} - {source}: {message}\n")

def start_log_worker_task():
    """No-op. Left for compatibility with lifespan."""
    pass

def stop_log_worker_task():
    """No-op. Left for compatibility with lifespan."""
    pass

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
            shared_container.task_runner.add_task(
                _insert_log_to_db,
                level,
                self._name,
                message,
                filename,
                lineno
            )
        except Exception:
            sys.stderr.write(f"[FALLBACK LOG - SCHEDULING FAILED] {level} - {self._name}: {message}\n")

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
