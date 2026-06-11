"""
Allows unverified users to request a fresh 6-digit OTP if their previous one expired.
To prevent malicious actors from discovering which emails are registered, this usecase
fails silently (returns without error) if the email doesn't exist or is already verified.
"""
from src.authentication.core.ports import UserRepositoryPort
from src.shared.core.ports.logger import LoggerPort
from src.authentication.core.ports.email_sender import EmailSenderPort
from src.shared.core.ports.cache import CachePort
from typing import Generic, TypeVar
import hashlib
import time
import secrets
from src.shared.config import token_settings
from src.authentication.core.utils import hash_otp


SessionType = TypeVar("SessionType")
class RequestNewVerificationEmailUseCase(Generic[SessionType]):
    """Handles requesting a new verification OTP."""
    
    def __init__(
        self, user_repo: UserRepositoryPort, logger: LoggerPort, 
        email_sender: EmailSenderPort, cache: CachePort
    ):
        self._user_repo = user_repo
        self._logger = logger
        self._email_sender = email_sender
        self._cache = cache
        
    async def execute(self, session: SessionType, email: str) -> None:
        user = await self._user_repo.find_by_email(session, email)
        if not user:
            # User doesn't exist. Silently return to prevent email enumeration.
            return
            
        if user.is_verified:
            # User is already verified. Silently return to prevent email enumeration.
            return
            
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        redis_key = f"pending_reg:{email_hash}"
        
        existing_payload = await self._cache.get_dict(redis_key)
        if not existing_payload:
            # The pending registration expired. User must register again.
            return
            
        otp = f"{secrets.randbelow(1000000):06d}"
        otp_expires_at = int(time.time()) + token_settings.OTP_EXPIRATION_SECONDS
        
        payload = {
            "otp": hash_otp(otp),
            "otp_expires_at": otp_expires_at,
            "pending_password_hash": existing_payload.get("pending_password_hash"),
            "pending_name": existing_payload.get("pending_name"),
            "attempts": existing_payload.get("attempts", 0)
        }
        
        # Save to Redis, refreshing the 15 minute total TTL
        await self._cache.set_dict(redis_key, payload, token_settings.OTP_RESEND_WINDOW_SECONDS) 
        
        await self._email_sender.send_verification_email(email, otp)
        await self._logger.info(f"Resent verification OTP to pending user {email}")
