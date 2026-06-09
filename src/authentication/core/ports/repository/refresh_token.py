"""
Port: Refresh Token Repository

This module defines the interface for reading and writing long-lived refresh tokens.
"""
from typing import Protocol, TypeVar
from src.authentication.core.domain import UserIdentity
from uuid import UUID
from src.authentication.core.domain.session import ClientMetadata, ActiveSession

SessionType = TypeVar("SessionType", contravariant=True)

class RefreshTokenRepositoryPort(Protocol[SessionType]):
    """Interface for managing long-lived refresh tokens."""

    async def validate(self, session: SessionType, token: str, client_meta: ClientMetadata | None = None) -> tuple[UserIdentity | None, str | None]:
        """
        Validate a refresh token.
        Returns (user_identity, new_token).
        new_token is set if the token was rotated, None otherwise.
        """
        ...
        
    async def get_active_sessions(self, session: SessionType, user_id: str, current_token: str | None = None) -> list[ActiveSession]:
        """Returns all active token families (sessions) for a user."""
        ...

    async def create(self, session: SessionType, user_id: str, family_id: UUID | None = None, auth_provider: str = "local", client_meta: ClientMetadata | None = None) -> str:
        """Create a new refresh token for the given user. Returns the raw token string."""
        ...

    async def revoke(self, session: SessionType, token: str) -> None:
        """Revoke a refresh token and its entire rotation family."""
        ...

    async def revoke_by_family(self, session: SessionType, family_id: str) -> None:
        """Revoke a specific token family (logout from device)."""
        ...

    async def cleanup_expired(self, session: SessionType) -> int:
        """Delete all expired and used tokens. Returns count deleted."""
        ...
