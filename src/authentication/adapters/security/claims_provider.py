"""
A default, empty implementation of the ClaimsProviderPort.
Returns an empty dictionary so that the default template works out-of-the-box
without requiring a separate Authorization domain to exist.
"""
from typing import Any
from src.authentication.core.ports.security.claims_provider import ClaimsProviderPort

class NullClaimsProviderAdapter(ClaimsProviderPort):
    """Returns no extra claims."""
    
    async def get_custom_claims(self, session: Any, user_id: str) -> dict[str, Any]:
        return {}
