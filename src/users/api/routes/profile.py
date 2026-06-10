"""
Exposes HTTP endpoints for managing user profiles.
Handles fetching, updating, and completely deleting a user's account.
During deletion, it ensures the current session is securely terminated by blacklisting the active JWT.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.shared.infrastructure.sql.connection import get_db
from src.authentication.api.dependencies import get_current_user, verify_csrf, get_jwt_payload
from src.authentication.core.domain import UserIdentity
from src.authentication.api.container import get_container
from src.users.api.container import user_profile_repository
from src.users.core.domain.exceptions import UserNotFoundException
from src.shared.config import rate_limit_settings, token_settings
from src.shared.api.utils import delete_refresh_token_cookie
from src.shared.api.dependencies import limiter
from datetime import datetime, timezone
from src.users.core.domain.profile import UserProfile


router = APIRouter()

class ProfileUpdate(BaseModel):
    name: str | None = None
    picture: str | None = None
    receive_updates: bool | None = None


@router.get("/me", response_model=UserProfile)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def get_profile(
    request: Request,
    current_user: Annotated[UserIdentity, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Fetch the current user's profile information.
    
    Requires a valid JWT Access Token. Returns basic profile details like the user's ID, email, display name, and profile picture URL.
    
    **Returns:**
    The user's profile object.
    """
    profile = await user_profile_repository.get_profile(db, current_user.id)
    if not profile:
        raise UserNotFoundException()
    return profile


@router.patch("/me", dependencies=[Depends(verify_csrf)], response_model=UserProfile)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def update_profile(
    request: Request,
    body: ProfileUpdate,
    current_user: Annotated[UserIdentity, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update the current user's profile information.
    
    Allows the user to modify their display name or profile picture URL. Fields omitted from the payload will remain unchanged.
    
    **Returns:**
    The updated user profile object.
    """
    profile = await user_profile_repository.get_profile(db, current_user.id)
    if not profile:
        raise UserNotFoundException()

    updated = await user_profile_repository.update_profile(
        db,
        current_user.id,
        name=body.name if body.name is not None else profile.name,
        picture=body.picture if body.picture is not None else profile.picture,
        receive_updates=body.receive_updates if body.receive_updates is not None else profile.receive_updates
    )
    return updated


@router.delete("/me", dependencies=[Depends(verify_csrf)])
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def delete_me(
    request: Request,
    current_user: Annotated[UserIdentity, Depends(get_current_user)],
    jwt_payload: Annotated[dict, Depends(get_jwt_payload)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Permanently delete the current user's account.
    
    This endpoint initiates a cascading deletion of the user's data:
    1. Deletes the core User record (which cascades to delete OAuth links, passwords, and sessions in the database).
    2. Blacklists the current JWT Access Token in Redis to immediately terminate the active session.
    3. Deletes the `refresh_token` HTTP-Only cookie from the browser.
    
    **Warning:** This action is irreversible.
    
    **Returns:**
    A 204 No Content response upon successful deletion.
    """
    
    # 1. Delete user from database (this cascades to oauth accounts, passwords, and refresh tokens)
    await user_profile_repository.delete_user(db, current_user.id)
    
    # 2. Blacklist the current access token
    jti = jwt_payload.get("jti")
    exp = jwt_payload.get("exp")
    if jti and exp:
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now
        if ttl > 0:
            max_ttl = token_settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60
            ttl = min(ttl, max_ttl)
            await get_container().cache_adapter.set_string(f"blacklist:{jti}", "1", ttl)
            
    # 3. Clear the refresh token cookie
    response = Response(status_code=204)
    delete_refresh_token_cookie(response)
    
    return response
