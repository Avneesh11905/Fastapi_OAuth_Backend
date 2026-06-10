"""
Exposes HTTP endpoints for refreshing access tokens.
Reads the long-lived refresh token from a secure, HttpOnly cookie,
triggers the `RefreshSessionUseCase`, and returns a fresh short-lived access token.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.config import rate_limit_settings
from src.shared.infrastructure.sql.connection import get_db
from src.authentication.api.usecase_dependencies import get_refresh_session_usecase
from src.authentication.core.usecases import RefreshSessionUseCase
from src.authentication.api.dependencies import verify_csrf
from src.shared.api.dependencies import limiter
from src.shared.api.utils import set_refresh_token_cookie, delete_refresh_token_cookie, extract_client_metadata

from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str

router = APIRouter()

@router.post("/refresh", dependencies=[Depends(verify_csrf)], response_model=TokenResponse)
@limiter.limit(rate_limit_settings.REFRESH_RATE_LIMIT)
async def refresh(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    usecase: Annotated[RefreshSessionUseCase, Depends(get_refresh_session_usecase)]
):
    """
    Refresh the session and obtain a new Access Token.
    
    This endpoint reads the HTTP-Only `refresh_token` cookie. It performs **Token Rotation** by invalidating the old refresh token and issuing a brand new one to prevent replay attacks.
    
    If the refresh token is valid, it returns a fresh 15-minute Access Token in the JSON body, and sets the new Refresh Token in the cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return Response(status_code=204)

    client_meta = extract_client_metadata(request)
    access_token, new_refresh_token = await usecase.execute(db, refresh_token, client_meta=client_meta)
    await db.commit()
    
    if not access_token:
        response = Response(status_code=401)
        delete_refresh_token_cookie(response)
        return response

    response = JSONResponse(content={"access_token": access_token})

    if new_refresh_token:
        set_refresh_token_cookie(response, new_refresh_token, request)

    return response
