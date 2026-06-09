"""
Port: Access Token

This module defines the interface (Port) for short-lived access tokens.
"""
from typing import Protocol, Any
from src.authentication.core.domain import UserIdentity

class AccessTokenPort(Protocol):
    """Interface for creating and verifying short-lived access tokens."""

    def create(self, user: UserIdentity, extra_claims: dict[str, Any] | None = None) -> str: ...
    def verify(self, token: str) -> tuple[UserIdentity | None, dict | None]:
        """Verifies the access token and returns (UserIdentity, payload_dict) if valid, or (None, None) if invalid/expired."""
        ...
