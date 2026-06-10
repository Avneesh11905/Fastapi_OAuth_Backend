"""
Exposes HTTP endpoints for the email verification flow.
Handles validating the 6-digit OTP sent via email and allowing users to request a new OTP if it expired.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.sql.connection import get_db
from src.authentication.api.usecase_dependencies import get_verify_email_usecase, get_request_new_verification_email_usecase
from src.authentication.core.usecases import VerifyEmailUseCase, RequestNewVerificationEmailUseCase
from src.shared.api.dependencies import limiter
from src.shared.config import rate_limit_settings

from src.authentication.api.schemas import VerifyEmailRequest, RequestNewVerificationEmail, MessageResponse
from src.shared.api.utils import build_auth_response
router = APIRouter()


@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def verify_email(
    request: Request,
    req: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    usecase: Annotated[VerifyEmailUseCase, Depends(get_verify_email_usecase)]
):
    """
    Verify a user's email address using a 6-digit OTP.
    
    This endpoint accepts the email address and the 6-digit One Time Password (OTP) that was emailed to the user upon registration.
    - If the OTP matches and hasn't expired (5-minute window), the user is permanently created in the database and marked as verified.
    - Once verified, the user can proceed to the `/login/local` endpoint.
    
    **Returns:**
    A success message upon successful verification.
    """
    user, refresh_token = await usecase.execute(db, req.email, req.otp)
    await db.commit()
    return build_auth_response(refresh_token, message="Email verified successfully", request=request)

@router.post("/verify-email/resend", response_model=MessageResponse)
@limiter.limit(rate_limit_settings.DEFAULT_RATE_LIMIT)
async def resend_verification(
    request: Request,
    req: RequestNewVerificationEmail,
    db: Annotated[AsyncSession, Depends(get_db)],
    usecase: Annotated[RequestNewVerificationEmailUseCase, Depends(get_request_new_verification_email_usecase)]
):
    """
    Resend the 6-digit verification OTP.
    
    If the user's previous OTP expired or they didn't receive the email, this endpoint generates a fresh 6-digit OTP and extends the verification window for another 5 minutes.
    The new OTP is sent to the user's email address.
    
    **Returns:**
    A generic success message.
    """
    await usecase.execute(db, req.email)
    return MessageResponse(message="If the email is registered and unverified, a new OTP has been sent.")
