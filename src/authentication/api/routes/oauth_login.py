"""
Exposes HTTP endpoints for local email/password login.
Expects application/x-www-form-urlencoded data (OAuth2 standard) and triggers the `LoginLocalUserUseCase`.
Sets a secure HttpOnly cookie containing the Refresh Token upon success.
"""
from fastapi import HTTPException, APIRouter, Request
from src.authentication.infrastructure.oauth import PROVIDERS
from src.shared.api.dependencies import limiter
from src.shared.config import rate_limit_settings

router = APIRouter()

# Provider registry — To add a new provider, create a new file in infrastructure/oauth/providers/

@router.get("/login/{provider}")
@limiter.limit(rate_limit_settings.LOGIN_RATE_LIMIT)
async def login(provider: str, request: Request):
    """Generic login route that redirects to the appropriate OAuth provider."""
    oauth_client = PROVIDERS.get(provider)
    if not oauth_client:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    return await oauth_client.authorize_redirect(
        request,
        request.url_for("oauth_callback", provider=provider),
    )
