"""
Port: Logger

This module defines the interface (Port) for logger.
Core business logic relies on these interfaces rather than concrete implementations.
"""
from typing import Protocol


class LoggerPort(Protocol):
    """Interface for structured async logging."""

    async def trace(self, message: str) -> None:
        """Finest-grained informational events."""
        ...

    async def debug(self, message: str) -> None:
        """Detailed diagnostic information for debugging."""
        ...

    async def info(self, message: str) -> None:
        """General informational messages about application progress."""
        ...

    async def warning(self, message: str) -> None:
        """Potentially harmful situations that deserve attention."""
        ...

    async def error(self, message: str) -> None:
        """Error events that allow the application to continue running."""
        ...

    async def fatal(self, message: str) -> None:
        """Severe errors that will likely cause the application to abort."""
        ...
