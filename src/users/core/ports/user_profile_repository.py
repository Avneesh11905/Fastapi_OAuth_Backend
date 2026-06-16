"""
Defines the interface (Port) for interacting with user profile data.
Abstracts away the underlying database implementation so that business logic can remain pure.
"""
from typing import Protocol, Any
from src.users.core.domain import UserProfile
from uuid import UUID

class UserProfileRepositoryPort(Protocol):
    async def get_profile(self, session: Any, user_id: UUID) -> UserProfile | None:
        """Fetch the user's profile."""
        ...

    async def update_profile(
        self, session: Any, user_id: UUID, name: str | None = None, picture: str | None = None, receive_updates: bool | None = None
    ) -> UserProfile:
        """Update a user's display name and picture."""
        ...

    async def delete_user(self, session: Any, user_id: UUID) -> None:
        """Delete a user and all of their associated data."""
        ...
