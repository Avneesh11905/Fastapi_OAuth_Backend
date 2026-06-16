"""
Module: Dependencies
"""
import hashlib

# --- Security dependencies ---
import hmac
from typing import Annotated

from fastapi import Depends, Request
from itsdangerous import URLSafeSerializer
from itsdangerous.exc import BadSignature

from src.authentication.container import get_container
from src.authentication.core.domain import UserIdentity
from src.authentication.core.domain.exceptions import (
    CSRFValidationException,
    InvalidTokenException,
    NotAuthenticatedException,
)
from src.authentication.core.ports.security.access_token import AccessTokenPort
from src.shared.config import app_settings
from src.shared.core.ports.cache import CachePort


async def verify_csrf(request: Request):
    """
    Verifies the Double Submit Cookie for CSRF protection.
    The frontend must extract the non-HttpOnly 'csrf_token' cookie and attach it as the 'X-CSRF' header.
    """
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF")
    refresh_token = request.cookies.get("refresh_token")
    
    if not csrf_cookie or not csrf_header:
        raise CSRFValidationException("Missing CSRF token in cookie or header")
        
    # Prevent timing attacks during comparison
    if not hmac.compare_digest(csrf_cookie, csrf_header):
        raise CSRFValidationException("Invalid CSRF token")
        
    if not refresh_token:
        return  # No session to protect, so CSRF is not applicable

    csrf_signer = URLSafeSerializer(app_settings.SESSION_SECRET, salt="csrf-token")
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    try:
        bound_hash = csrf_signer.loads(csrf_cookie)
        if not hmac.compare_digest(bound_hash, refresh_token_hash):
            raise CSRFValidationException("CSRF token is not bound to the current session")
    except BadSignature:
        raise CSRFValidationException("Invalid or corrupted CSRF token")


def get_access_token_adapter() -> AccessTokenPort:
    return get_container().access_token_adapter

def get_cache_adapter() -> CachePort:
    return get_container().cache_adapter

async def get_jwt_payload(
    request: Request,
    access_token_adapter: Annotated[AccessTokenPort, Depends(get_access_token_adapter)],
    cache_adapter: Annotated[CachePort, Depends(get_cache_adapter)]
) -> dict:
    """Extracts, verifies, and returns the raw JWT payload (including custom claims)."""

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise NotAuthenticatedException()

    token = auth_header.removeprefix("Bearer ")

    user, payload = access_token_adapter.verify(token)
    if not payload or not payload.get("jti") or not payload.get("sub") or not user:
        raise InvalidTokenException("Access token expired or invalid")

    jti = payload["jti"]

    if await cache_adapter.get_string(f"blacklist:{jti}"):
        raise InvalidTokenException("Access token revoked")

    # Attach the strongly typed UserIdentity so downstream dependencies can access it if needed
    payload["_user_obj"] = user
    return payload


async def get_current_user(payload: Annotated[dict, Depends(get_jwt_payload)]) -> UserIdentity:
    """Returns the strongly typed UserIdentity object for normal API endpoints."""
    return payload["_user_obj"]
