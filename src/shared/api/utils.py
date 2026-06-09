"""
Contains shared utility functions for the API layer.
Includes custom response formatters and generic error handlers to maintain a consistent JSON structure across the entire app.
"""
from fastapi.responses import Response, JSONResponse, RedirectResponse
from fastapi import Request
from src.shared.config import token_settings, url_settings, cookie_settings
from src.authentication.core.domain.session import ClientMetadata

import secrets

def extract_client_metadata(request: Request) -> ClientMetadata:
    """Extracts IP address and User-Agent from the incoming request."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ClientMetadata(ip_address=ip, user_agent=ua)

def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """Standardized utility to set the refresh token cookie and CSRF double-submit cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=cookie_settings.HTTP_ONLY,
        secure=cookie_settings.SECURE,
        samesite=cookie_settings.SAMESITE, # type: ignore
        max_age=token_settings.REFRESH_TOKEN_LIFETIME_DAYS * 86400,
        domain=cookie_settings.DOMAIN,
        path=cookie_settings.PATH,
    )
    
    # Set the CSRF double-submit cookie (MUST be readable by JS)
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=cookie_settings.SECURE,
        samesite=cookie_settings.SAMESITE, # type: ignore
        domain=cookie_settings.DOMAIN,
        path=cookie_settings.PATH,
    )

def delete_refresh_token_cookie(response: Response) -> None:
    """Standardized utility to delete the session cookies."""
    response.delete_cookie(
        key="refresh_token",
        httponly=cookie_settings.HTTP_ONLY,
        secure=cookie_settings.SECURE,
        samesite=cookie_settings.SAMESITE, # type: ignore
        domain=cookie_settings.DOMAIN,
        path=cookie_settings.PATH,
    )
    response.delete_cookie(
        key="csrf_token",
        httponly=False,
        secure=cookie_settings.SECURE,
        samesite=cookie_settings.SAMESITE, # type: ignore
        domain=cookie_settings.DOMAIN,
        path=cookie_settings.PATH,
    )

def build_auth_response(refresh_token: str, message: str = "Authenticated successfully") -> JSONResponse:
    """Builds a standardized JSONResponse indicating success, with the refresh token attached."""
    response = JSONResponse(content={"message": message})
    set_refresh_token_cookie(response, refresh_token)
    return response

def build_auth_redirect(refresh_token: str) -> RedirectResponse:
    """Builds a redirect to the frontend with the refresh token cookie attached."""
    response = RedirectResponse(url=url_settings.FRONTEND_URL)
    set_refresh_token_cookie(response, refresh_token)
    return response
