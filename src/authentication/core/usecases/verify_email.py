"""
Validates a short-lived 6-digit OTP sent to the user's email during registration.
If the OTP matches the one stored in the ephemeral cache (Redis), the user
is permanently marked as verified in the database, and the Welcome Email is dispatched.
"""
from src.authentication.core.ports import UserRepositoryPort
from src.shared.core.ports.logger import LoggerPort
from src.shared.core.ports.cache import CachePort
from src.authentication.core.ports.email_sender import EmailSenderPort
from typing import Protocol, Any, Generic, TypeVar
import hashlib
import time
from src.authentication.core.utils import verify_otp_hash
from src.authentication.core.ports import RefreshTokenRepositoryPort
from src.authentication.core.domain import UserIdentity
from src.authentication.core.domain.session import ClientMetadata

class UoWPort(Protocol):
    session: Any

class VerifyEmailUseCase[UoWType: UoWPort]:
    """Handles verification of the 6-digit OTP for email verification."""
    
    def __init__(
        self, user_repo: UserRepositoryPort, cache: CachePort, logger: LoggerPort, email_sender: EmailSenderPort, refresh_repo: RefreshTokenRepositoryPort
    ):
        self._user_repo = user_repo
        
        self._cache = cache
        self._logger = logger
        self._email_sender = email_sender
        self._refresh_repo = refresh_repo
        
    async def execute(self, uow: UoWType, email: str, otp: str, client_meta: ClientMetadata | None = None) -> tuple[UserIdentity, str]:
        """
        Verifies the OTP for the given email using the Redis-First flow.
        If valid, saves the user to the DB and sends welcome email.
        Raises Domain Exceptions if invalid or expired.
        """
        from src.authentication.core.domain.exceptions import InvalidCredentialsException, InvalidTokenException
        
        # 1. Check if user is in DB
        user = await self._user_repo.find_by_email(uow.session, email)
        if not user:
            await self._logger.warning(f"Verification failed: User {email} not found")
            raise InvalidCredentialsException(detail="User not found")
            
        if user.is_verified:
            await self._logger.warning(f"Verification failed: User {email} is already verified")
            raise InvalidCredentialsException(detail="Email is already verified. Please log in.")

        # 2. Fetch pending registration payload from Redis
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        redis_key = f"pending_reg:{email_hash}"
        payload = await self._cache.get_dict(redis_key)
        
        if not payload:
            await self._logger.warning(f"Verification failed: No pending registration found for {email}")
            raise InvalidCredentialsException(detail="Invalid OTP or email, or registration expired")
            
        # 3. Check 5-minute expiry FIRST
        current_time = int(time.time())
        otp_expires_at = int(payload.get("otp_expires_at", 0))
        if current_time > otp_expires_at:
            await self._logger.warning(f"Verification failed: OTP expired for {email}")
            raise InvalidTokenException(detail="OTP has expired. Please request a new one.")
            
        # 4. Increment attempt count atomically using the dedicated counter key
        from src.shared.config import verification_settings
        attempt_key = f"otp_attempts:{email_hash}"
        attempts = await self._cache.incr(attempt_key, ttl=verification_settings.OTP_RESEND_WINDOW_SECONDS)

        if attempts > verification_settings.OTP_MAX_ATTEMPTS:
            await self._cache.delete_key(redis_key)
            await self._logger.warning(f"Verification failed: Too many OTP attempts for {email}")
            raise InvalidTokenException(detail="Too many failed attempts. Please request a new OTP.")
            
        # 5. Compare OTP securely
        stored_otp_hash = str(payload.get("otp", ""))
        provided_otp = str(otp)
        
        if not verify_otp_hash(provided_otp, stored_otp_hash):
            await self._logger.warning(f"Verification failed: Incorrect OTP for {email}")
            raise InvalidTokenException(detail="Invalid OTP")
            
        # 6. Success! Mark the user as verified in PostgreSQL
        await self._user_repo.verify_user_email(uow.session, user.id, name=payload.get("pending_name"))
        
        pending_password_hash = payload.get("pending_password_hash")
        if pending_password_hash:
            await self._user_repo.update_password(uow.session, user.id, pending_password_hash)
        
        # Issue a refresh token to auto-login
        token = await self._refresh_repo.create(uow.session, user.id, client_meta=client_meta)
        
        # 6. Clean up Redis (both registration payload and attempts counter)
        await self._cache.delete_key(redis_key)
        await self._cache.delete_key(attempt_key)
        
        # 7. Send the welcome email
        await self._email_sender.send_welcome_email(user.email, user.name)
        
        await self._logger.info(f"User {user.id} email verified successfully")
        return user, token
