"""
Defines the interface (Port) for interacting with user profile data.
Abstracts away the underlying database implementation so that business logic can remain pure.
"""
from typing import Protocol, Any
from src.users.core.domain import UserProfile

class UserProfileRepositoryPort(Protocol):
    async def get_profile(self, session: Any, user_id: str) -> UserProfile | None:
        """Fetch the user's profile."""
        ...

    async def update_profile(
        self, session: Any, user_id: str, name: str | None, picture: str | None, receive_updates: bool
    ) -> UserProfile:
        """Update a user's display name and picture."""
        ...

    async def delete_user(self, session: Any, user_id: str) -> None:
        """Delete a user and all of their associated data."""
        ...
