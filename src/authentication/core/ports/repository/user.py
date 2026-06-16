"""
Port: User Repository

This module defines the interface for reading and writing user data.
"""
from typing import Protocol, TypeVar
from src.authentication.core.domain import UserIdentity
from uuid import UUID

SessionType = TypeVar('SessionType', contravariant=True)

class UserRepositoryPort(Protocol[SessionType]):
    """Interface for querying and modifying user records."""

    async def find_by_oauth(self, session: SessionType, provider: str, oauth_sub: str) -> UserIdentity | None:
        """Look up a user by their OAuth provider + subject ID. Returns None if not found."""
        ...

    async def find_by_email(self, session: SessionType, email: str) -> UserIdentity | None:
        """Look up a user by email. Returns None if not found."""
        ...

    async def find_password_hash(self, session: SessionType, user_id: UUID) -> str | None:
        """Look up the local password hash for a given user. Returns None if they only have OAuth."""
        ...

    async def create_user_with_oauth(
        self, session: SessionType, email: str, name: str | None, picture: str | None,
        provider: str, oauth_sub: str,
    ) -> UserIdentity:
        """Create a new user and link an OAuth account. Returns the new user identity."""
        ...

    async def link_oauth_account(
        self, session: SessionType, user_id: UUID, provider: str, oauth_sub: str,
    ) -> None:
        """Link a new OAuth provider to an existing user."""
        ...

    async def create_user_with_password(
        self, session: SessionType, email: str, name: str | None, password_hash: str | None, is_verified: bool = False
    ) -> UserIdentity:
        """Create a new user and link a local password. Returns the new user identity."""
        ...

    async def update_password(self, session: SessionType, user_id: UUID, password_hash: str) -> None:
        """Update or insert a password for a given user ID."""
        ...

    async def disable_local_login(self, session: SessionType, user_id: UUID) -> None:
        """Disable local password login for a given user ID."""
        ...

    async def verify_user_email(self, session: SessionType, user_id: UUID, name: str | None = None) -> None:
        """Mark a user's email as verified. Updates name if provided."""
        ...

    async def cleanup_unverified_users(self, session: SessionType, hours_old: int = 24) -> int:
        """Delete unverified users older than the specified hours. Returns number of deleted rows."""
        ...

    async def undelete_user(self, session: SessionType, user_id: UUID) -> None:
        """Restore a soft-deleted user."""
        ...

    async def cleanup_soft_deleted_users(self, session: SessionType, days_old: int = 30) -> int:
        """Permanently delete soft-deleted users older than the specified days. Returns number of deleted rows."""
        ...
