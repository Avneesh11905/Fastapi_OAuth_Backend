"""
A default, empty implementation of the ClaimsProviderPort.
Returns an empty dictionary so that the default template works out-of-the-box
without requiring a separate Authorization domain to exist.
"""
from uuid import UUID

from src.authentication.core.ports.security.claims_provider import ClaimsProviderPort


class NullClaimsProviderAdapter[SessionType](ClaimsProviderPort[SessionType]):
    """Returns no extra claims."""
    
    async def get_custom_claims(self, session: SessionType, user_id: UUID) -> dict[str, object]:
        return {}
