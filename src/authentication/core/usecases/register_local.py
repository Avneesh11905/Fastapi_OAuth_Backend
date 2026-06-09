"""
Orchestrates the local registration flow.
Responsible for checking email uniqueness, hashing the user's password,
persisting the new user, and triggering the OTP email verification process.
The user is created immediately but flagged as `is_verified=False` until OTP succeeds.
"""
from src.authentication.core.ports import UserRepositoryPort
from src.authentication.core.ports import PasswordHasherPort
from src.shared.core.ports.logger import LoggerPort
from src.authentication.core.ports.email.email_sender import EmailSenderPort
from src.authentication.core.ports.cache.cache import CachePort
from typing import Generic, TypeVar
import hashlib
import time
import secrets
from src.shared.config import token_settings
from src.authentication.core.utils import hash_otp


SessionType = TypeVar("SessionType")
class RegisterLocalUserUseCase(Generic[SessionType]):
    """Handles user registration with email and password."""

    def __init__(
        self, user_repo: UserRepositoryPort, hasher: PasswordHasherPort, 
        logger: LoggerPort, email_sender: EmailSenderPort, 
        cache: CachePort
    ):
        self._user_repo = user_repo
        
        self._hasher = hasher
        self._logger = logger
        self._email_sender = email_sender
        self._cache = cache

    async def execute(self, session: SessionType, email: str, password: str, name: str | None) -> None:
        """
        Register a new user and trigger email verification.
        Saves the pending registration data to Redis (Redis-First Flow).
        Raises ValueError if email already exists in DB.
        """
        # 1. Check if email exists in PostgreSQL
        existing = await self._user_repo.find_by_email(session, email)
        if existing and existing.is_verified:
            await self._logger.warning(f"Registration failed: Email {email} already registered and verified")
            from src.authentication.core.domain import EmailAlreadyRegisteredException
            raise EmailAlreadyRegisteredException()

        # 2. Hash password securely
        hashed = await self._hasher.hash_password(password)

        if not existing:
            # 3a. Save pending user to PostgreSQL directly, but without a password.
            await self._user_repo.create_user_with_password(
                session=session, email=email, name=name, password_hash=None, is_verified=False
            )
        else:
            # 3b. DO NOT update password for unverified user here to prevent pre-hijacking.
            pass
        
        # 3. Generate 6-digit OTP and calculate 5-minute expiry
        otp = f"{secrets.randbelow(1000000):06d}"
        otp_expires_at = int(time.time()) + token_settings.OTP_EXPIRATION_SECONDS
        
        # 4. Construct pending payload with HASHED OTP and the pending password
        payload = {
            "otp": hash_otp(otp),
            "otp_expires_at": otp_expires_at,
            "pending_password_hash": hashed,
            "pending_name": name
        }
        
        # 5. Save OTP to Redis for 15 minutes (resend window)
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        await self._cache.set_dict(f"pending_reg:{email_hash}", payload, token_settings.OTP_RESEND_WINDOW_SECONDS) 
        
        # 6. Dispatch email
        await self._email_sender.send_verification_email(email, otp)
        
        await self._logger.info(f"Pending registration cached for {email}. Verification OTP sent.")
