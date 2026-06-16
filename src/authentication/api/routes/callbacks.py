"""
Exposes HTTP endpoints for OAuth provider redirects.
When Google/GitHub sends the user back, this route captures the authorization code,
exchanges it for user details, and triggers the `OAuthCallbackUseCase` to establish a session.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from src.shared.infrastructure.sql.uow import SQLAlchemyUnitOfWork, get_uow
from src.authentication.infrastructure.oauth import PROVIDERS, PARSERS
from src.authentication.api.usecase_dependencies import get_oauth_callback_usecase
from src.authentication.core.usecases import OAuthCallbackUseCase

from src.authentication.core.domain.exceptions import InvalidProviderException, OAuthFailedException
from src.shared.api.dependencies import limiter
from src.shared.config import rate_limit_settings
from src.shared.api.utils import build_auth_redirect, extract_client_metadata
router = APIRouter()


@router.get("/callback/{provider}", include_in_schema=False)
@limiter.limit(rate_limit_settings.LOGIN_RATE_LIMIT)
async def oauth_callback(
    provider: str,
    request: Request,
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[OAuthCallbackUseCase, Depends(get_oauth_callback_usecase)]
):
    """Handles the OAuth callback from the provider."""
    oauth_client = PROVIDERS.get(provider)
    if not oauth_client:
        raise InvalidProviderException(f"Invalid provider: {provider}")

    try:
        # Trade the code for an access token
        token = await oauth_client.authorize_access_token(request)
        # Parse the provider-specific token into our standard format
        parser = PARSERS.get(provider)
        if not parser:
            raise InvalidProviderException(f"No parser found for provider: {provider}")
        user_info = await parser(oauth_client, token)
    except InvalidProviderException:
        raise
    except Exception:
        raise OAuthFailedException(f"Failed to authenticate with {provider}")

    client_meta = extract_client_metadata(request)
    async with uow:
        user, refresh_token = await usecase.execute(uow, user_info, client_meta=client_meta)
    
    return build_auth_redirect(refresh_token, request)
