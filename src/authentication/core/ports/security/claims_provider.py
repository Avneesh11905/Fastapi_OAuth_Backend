"""
Defines the interface for injecting custom claims (like authorization roles) into an access token.
This allows the Authentication domain to remain ignorant of Authorization details, while still
supporting rich JWTs via Dependency Injection.
"""
from typing import Protocol, Any
from uuid import UUID

class ClaimsProviderPort(Protocol):
    async def get_custom_claims(self, session: Any, user_id: UUID) -> dict[str, Any]:
        """Returns a dictionary of custom claims to inject into the JWT."""
        ...
