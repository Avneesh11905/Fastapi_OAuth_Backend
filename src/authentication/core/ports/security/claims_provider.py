"""
Defines the interface for injecting custom claims (like authorization roles) into an access token.
This allows the Authentication domain to remain ignorant of Authorization details, while still
supporting rich JWTs via Dependency Injection.
"""
from typing import Protocol
from uuid import UUID


class ClaimsProviderPort[SessionType](Protocol):
    async def get_custom_claims(self, session: SessionType, user_id: UUID) -> dict[str, object]:
        """Returns a dictionary of custom claims to inject into the JWT."""
        ...
