"""
Exposes HTTP endpoints for managing user sessions (devices).
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.sql.connection import get_db
from src.authentication.core.usecases import ListSessionsUseCase, RevokeSessionUseCase
from src.authentication.api.usecase_dependencies import get_list_sessions_usecase, get_revoke_session_usecase
from src.authentication.api.dependencies import get_current_user
from src.authentication.api.schemas import SessionResponse
from src.authentication.core.domain import UserIdentity
from src.shared.api.dependencies import limiter
from src.shared.config import rate_limit_settings


router = APIRouter()

@router.get("/sessions", response_model=list[SessionResponse])
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def list_sessions(
    request: Request,
    user: Annotated[UserIdentity, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    usecase: Annotated[ListSessionsUseCase, Depends(get_list_sessions_usecase)]
):
    """
    List all active sessions (devices) for the current user.
    
    This endpoint queries the database for all active refresh token families associated with the user.
    It returns metadata about each session, such as:
    - `ip_address`: The IP address where the session originated.
    - `user_agent`: The browser or device used.
    - `created_at`: When the session was first established.
    - `last_active`: When the session was last refreshed.
    - `is_current`: A boolean indicating if this specific session matches the refresh token provided in the current request's cookies.
    
    **Returns:**
    A list of session metadata objects.
    """
    current_token = request.cookies.get("refresh_token")
    sessions = await usecase.execute(db, user.id, current_token)
    return sessions

@router.delete("/sessions/{family_id}", status_code=204)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def revoke_session(
    family_id: str,
    request: Request,
    user: Annotated[UserIdentity, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    usecase: Annotated[RevokeSessionUseCase, Depends(get_revoke_session_usecase)]
):
    """
    Revoke a specific session by its Family ID.
    
    This allows a user to remotely log out of other devices. It immediately invalidates the entire refresh token family associated with that device, forcing the device to re-authenticate on its next request.
    
    **Returns:**
    A 204 No Content response on success.
    Raises a 404 error if the session family ID does not exist or does not belong to the user.
    """
    try:
        await usecase.execute(db, user.id, family_id)
        await db.commit()
    except Exception as e:
        from src.authentication.core.domain.exceptions import SessionNotFoundException
        if isinstance(e, SessionNotFoundException):
            raise HTTPException(status_code=404, detail=str(e))
        raise e
