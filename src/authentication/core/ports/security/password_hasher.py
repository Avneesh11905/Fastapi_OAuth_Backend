"""
Port: Password Hasher

This module defines the interface (Port) for password hasher.
Core business logic relies on these interfaces rather than concrete implementations.
"""
from typing import Protocol


class PasswordHasherPort(Protocol):
    """Interface for securely hashing and verifying passwords."""

    async def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""
        ...

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored hash."""
        ...

    async def dummy_verify(self) -> None:
        """Simulate a password verification to prevent timing attacks."""
        ...
