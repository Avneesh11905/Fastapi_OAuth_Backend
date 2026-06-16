"""
Exposes HTTP endpoints for ending user sessions.
Extracts the active tokens from cookies and headers and delegates to the `LogoutUseCase` to invalidate them.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from src.shared.config import rate_limit_settings
from src.authentication.api.usecase_dependencies import get_logout_usecase
from src.authentication.core.usecases import LogoutUseCase
from src.authentication.api.dependencies import verify_csrf, get_current_user
from src.authentication.core.domain import UserIdentity
from src.shared.api.dependencies import limiter
from src.shared.infrastructure.sql.uow import SQLAlchemyUnitOfWork, get_uow
from src.shared.api.utils import delete_refresh_token_cookie

router = APIRouter()


@router.post("/logout", dependencies=[Depends(verify_csrf)])
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def logout(
    request: Request,
    user: Annotated[UserIdentity, Depends(get_current_user)],
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[LogoutUseCase, Depends(get_logout_usecase)]
):
    """
    Log out the current user and invalidate their session.
    
    This endpoint securely terminates the user's session by:
    1. Extracting the **Refresh Token** from the `refresh_token` HTTP-Only cookie.
    2. Extracting the **Access Token** from the `Authorization: Bearer <token>` header.
    3. Revoking the refresh token family in the database to prevent future use.
    4. Blacklisting the current access token in Redis until its natural expiration.
    5. Instructing the browser to delete the `refresh_token` cookie.
    
    **Returns:**
    A 200 OK response with a success message.
    """
    refresh_token = request.cookies.get("refresh_token")
    
    auth_header = request.headers.get("Authorization")
    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.removeprefix("Bearer ")
        
    async with uow:
        await usecase.execute(uow, refresh_token, access_token)

    response = JSONResponse(content={"message": "Logged out"})
    delete_refresh_token_cookie(response)
    return response
