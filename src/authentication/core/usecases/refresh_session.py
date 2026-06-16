"""
Maintains active user sessions securely without requiring re-authentication.
Validates an existing opaque refresh token against the database to ensure it hasn't 
expired or been revoked. On success, it implements Refresh Token Rotation by
invalidating the old token and issuing a brand new (Access Token, Refresh Token) pair.
"""

from src.authentication.core.domain.session import ClientMetadata
from src.authentication.core.ports import RefreshTokenRepositoryPort
from src.authentication.core.ports.security.access_token import AccessTokenPort
from src.authentication.core.ports.security.claims_provider import ClaimsProviderPort
from src.shared.core.ports.uow import UoWPort


class RefreshSessionUseCase[SessionType]:
    """Handles validating a refresh token and issuing a new access token."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort[SessionType], access_token: AccessTokenPort, claims_provider: ClaimsProviderPort):
        self._refresh_repo = refresh_repo
        self._access_token = access_token
        self._claims_provider = claims_provider
        
    async def execute(self, uow: UoWPort[SessionType], refresh_token: str, client_meta: ClientMetadata | None = None) -> tuple[str | None, str | None]:
        """
        Validates the refresh token and returns (new_access_token, new_refresh_token).
        Returns (None, None) if the refresh token is invalid.
        """
        user, new_refresh_token, family_id = await self._refresh_repo.validate(uow.session, refresh_token, client_meta=client_meta)
        if not user:
            return None, None
            
        custom_claims = await self._claims_provider.get_custom_claims(uow.session, user.id)
        # Embed the family_id so the middleware can check it against the Redis blacklist
        combined_claims: dict[str, object] = {"family_id": str(family_id)}
        if custom_claims:
            combined_claims.update(custom_claims)
        access_token = self._access_token.create(user, extra_claims=combined_claims)
        return access_token, new_refresh_token

