"""
Maintains active user sessions securely without requiring re-authentication.
Validates an existing opaque refresh token against the database to ensure it hasn't 
expired or been revoked. On success, it implements Refresh Token Rotation by
invalidating the old token and issuing a brand new (Access Token, Refresh Token) pair.
"""
from typing import Generic, TypeVar
from src.authentication.core.ports import RefreshTokenRepositoryPort
from src.authentication.core.ports.security.access_token import AccessTokenPort

from src.authentication.core.domain.session import ClientMetadata

from src.authentication.core.ports.security.claims_provider import ClaimsProviderPort

SessionType = TypeVar("SessionType")
class RefreshSessionUseCase(Generic[SessionType]):
    """Handles validating a refresh token and issuing a new access token."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort, access_token: AccessTokenPort, claims_provider: ClaimsProviderPort):
        self._refresh_repo = refresh_repo
        self._access_token = access_token
        self._claims_provider = claims_provider
        
    async def execute(self, session: SessionType, refresh_token: str, client_meta: ClientMetadata | None = None) -> tuple[str | None, str | None]:
        """
        Validates the refresh token and returns (new_access_token, new_refresh_token).
        Returns (None, None) if the refresh token is invalid.
        """
        user, new_refresh_token = await self._refresh_repo.validate(session, refresh_token, client_meta=client_meta)
        if hasattr(session, 'commit'):
            await session.commit()
        if not user:
            return None, None
            
        custom_claims = await self._claims_provider.get_custom_claims(session, user.id)
        access_token = self._access_token.create(user, extra_claims=custom_claims)
        return access_token, new_refresh_token
