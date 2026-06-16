"""
Terminates a user session securely.
It performs two distinct actions:
1. Revokes the long-lived refresh token in the database so no new access tokens can be minted.
2. Blacklists the short-lived access token in Redis (using its `jti`) until it expires naturally,
   preventing stolen tokens from being used immediately after logout.
"""
import jwt
from datetime import datetime, timezone

from src.authentication.core.ports import RefreshTokenRepositoryPort
from src.shared.core.ports.cache import CachePort
from src.shared.core.ports.uow import UoWPort
from src.shared.config import app_settings, token_settings

class LogoutUseCase[SessionType]:
    """Handles logging out a user by revoking the refresh token and blacklisting the access token."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort, cache: CachePort):
        self._refresh_repo = refresh_repo
        self._cache = cache
        
    async def execute(self, uow: UoWPort[SessionType], refresh_token: str | None, access_token: str | None) -> None:
        if refresh_token:
            await self._refresh_repo.revoke(uow.session, refresh_token)
            
        if access_token:
            try:
                payload = jwt.decode(access_token, key=app_settings.JWT_PUBLIC_KEY, algorithms=["RS256"], options={"verify_signature": True, "verify_exp": False})
                jti = payload.get("jti")
                exp = payload.get("exp")
                if jti and exp:
                    now = int(datetime.now(timezone.utc).timestamp())
                    ttl = exp - now
                    if ttl > 0:
                        max_ttl = token_settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60
                        ttl = min(ttl, max_ttl)
                        await self._cache.set_string(f"blacklist:{jti}", "1", ttl)
            except jwt.DecodeError as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to decode access token during logout: {e}")
