"""
Exposes HTTP endpoints for the password reset flow (both requesting a reset and executing it).
Translates HTTP requests into the corresponding `RequestPasswordResetUseCase` and `ExecutePasswordResetUseCase`.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request

from src.shared.infrastructure.sql.uow import SQLAlchemyUnitOfWork, get_uow
from src.authentication.api.usecase_dependencies import get_request_password_reset_usecase, get_execute_password_reset_usecase
from src.authentication.core.usecases import RequestPasswordResetUseCase, ExecutePasswordResetUseCase
from src.shared.api.dependencies import limiter
from src.shared.config import rate_limit_settings

from src.authentication.api.schemas import ForgotPasswordRequest, ResetPasswordRequest, MessageResponse
router = APIRouter(prefix="/password")



async def _execute_forgot_password_in_background(usecase: RequestPasswordResetUseCase, email: str) -> None:
    try:
        async with SQLAlchemyUnitOfWork() as uow:
            await usecase.execute(uow, email)
    except Exception:
        pass  # errors are logged inside the usecase

@router.post("/forgot", response_model=MessageResponse)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[RequestPasswordResetUseCase, Depends(get_request_password_reset_usecase)]
):
    """
    Request a password reset email.
    
    If the provided email exists in the system, this endpoint generates a secure, single-use reset token and emails a password reset link to the user.
    
    To prevent email enumeration attacks, this endpoint **always** returns a 200 OK status regardless of whether the email actually exists in the database. 
    The heavy lifting is done in a background task so the API responds instantly.
    
    **Returns:**
    A generic success message.
    """
    # We use TaskRunner so the API responds instantly and stays consistent with
    # all other background operations in this codebase (switchable to Celery)
    from src.authentication.container import get_container
    get_container().task_runner.add_task(_execute_forgot_password_in_background, usecase, body.email)
    
    # We always return 200 OK to prevent email enumeration
    return MessageResponse(message="If an account with that email exists, we sent a password reset link.")


@router.post("/reset", response_model=MessageResponse)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
    usecase: Annotated[ExecutePasswordResetUseCase, Depends(get_execute_password_reset_usecase)]
):
    """
    Execute a password reset using a valid token.
    
    This endpoint accepts the secure reset token (previously sent via email) along with a new password. 
    If the token is valid and hasn't expired, the user's password is cryptographically hashed and updated in the database.
    
    **Returns:**
    A success message upon successful password reset.
    Raises a 400 error if the token is invalid or expired.
    """
    async with uow:
        success = await usecase.execute(uow, body.token, body.new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return MessageResponse(message="Password successfully reset")
