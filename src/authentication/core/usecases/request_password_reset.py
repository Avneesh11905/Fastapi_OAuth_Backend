"""
Initiates the password reset process.
Generates a cryptographically secure 32-byte URL-safe token, stores it in Redis
with a 15-minute TTL, and dispatches an email to the user with a reset link.
Fails silently if the email does not exist to prevent enumeration attacks.
"""
import secrets
from typing import Protocol, Any, Generic, TypeVar
from src.authentication.core.ports import UserRepositoryPort
from src.authentication.core.ports.email_sender import EmailSenderPort
from src.shared.core.ports.cache import CachePort

class UoWPort(Protocol):
    session: Any

class RequestPasswordResetUseCase[UoWType: UoWPort]:
    """Handles generating a reset token and sending the email."""
    
    def __init__(self, user_repo: UserRepositoryPort, cache: CachePort, email_sender: EmailSenderPort, frontend_url: str):
        self.user_repo = user_repo
        self.cache = cache
        self.email_sender = email_sender
        self.frontend_url = frontend_url
        
    async def execute(self, uow: UoWType, email: str) -> None:
        user = await self.user_repo.find_by_email(uow.session, email)
        if not user or not user.is_verified:
            # Silently return to prevent email enumeration attacks
            return
            
        # Generate token
        token = secrets.token_urlsafe(32)
        
        # Store in cache with 15 minute TTL
        # Key: "pwd_reset:{token}" -> Value: user.id
        from src.shared.config import verification_settings
        await self.cache.set_string(f"pwd_reset:{token}", str(user.id), verification_settings.PASSWORD_RESET_EXPIRY_SECONDS)
        
        reset_url = f"{self.frontend_url}/reset-password?token={token}"
        await self.email_sender.send_password_reset_email(email, reset_url)
