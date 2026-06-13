"""
Exposes HTTP endpoints for local email/password registration.
Parses incoming JSON payloads, validates the data, and triggers the `RegisterLocalUserUseCase`.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response

from src.shared.infrastructure.sql.uow import SQLAlchemyUnitOfWork, get_uow
from src.authentication.api.usecase_dependencies import get_register_local_usecase, get_login_local_usecase, get_change_password_usecase
from src.authentication.core.usecases import RegisterLocalUserUseCase, LoginLocalUserUseCase, ChangePasswordUseCase
from src.authentication.api.dependencies import get_current_user, verify_csrf
from src.authentication.core.domain import UserIdentity

from src.shared.api.dependencies import limiter
from src.shared.config import rate_limit_settings

from src.authentication.api.schemas import RegisterRequest, LoginRequest, MessageResponse, ChangePasswordRequest
from src.shared.api.utils import build_auth_response, extract_client_metadata
router = APIRouter()



@router.post("/register", status_code=201, response_model=MessageResponse)
@limiter.limit(rate_limit_settings.LOGIN_RATE_LIMIT)
async def register(
    request: Request,
    req: RegisterRequest,
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[RegisterLocalUserUseCase, Depends(get_register_local_usecase)]
):
    """
    Register a new user with an email and password.
    
    This endpoint creates a new unverified user in the system. 
    It automatically generates a 6-digit OTP (One Time Password) and sends it to the provided email address via the Resend API.
    
    The user **cannot login** until they submit the OTP to the `/verify-email` endpoint.
    
    **Returns:**
    A success message instructing the user to check their email.
    """
    await usecase.execute(uow, req.email, req.password, req.name)
    pass # transaction handled by UoW
    return MessageResponse(message="Successfully registered! Please check your email for the 6-digit OTP code.")

@router.post("/login/local", response_model=MessageResponse)
@limiter.limit(rate_limit_settings.LOGIN_RATE_LIMIT)
async def login_local(
    request: Request,
    req: LoginRequest,
    response: Response,
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[LoginLocalUserUseCase, Depends(get_login_local_usecase)]
):
    """
    Authenticate a user and issue a new session.
    
    This endpoint verifies the user's email and password. If successful, it establishes a new secure session:
    
    1. A **Refresh Token** is generated and set as a Secure, HttpOnly cookie.
    
    **Note:** The user must have verified their email address before they can log in.
    """
    client_meta = extract_client_metadata(request)
    user, refresh_token = await usecase.execute(uow, req.email, req.password, client_meta=client_meta)
    pass # transaction handled by UoW
    return build_auth_response(refresh_token, request=request)

@router.patch("/password", response_model=MessageResponse, dependencies=[Depends(verify_csrf)])
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def change_password(
    request: Request,
    req: ChangePasswordRequest,
    current_user: Annotated[UserIdentity, Depends(get_current_user)],
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[ChangePasswordUseCase, Depends(get_change_password_usecase)]
):
    """
    Update the authenticated user's password.
    
    If the user already has a password, they must provide the correct `current_password`. 
    If they registered via OAuth and never set a password, `current_password` can be omitted.
    
    **Returns:**
    A success message.
    """
    await usecase.execute(uow, current_user.id, req.current_password, req.new_password)
    pass # transaction handled by UoW
    return MessageResponse(message="Password updated successfully")
