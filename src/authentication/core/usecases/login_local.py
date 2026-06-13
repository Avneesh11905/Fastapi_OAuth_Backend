"""
Orchestrates the local authentication flow.
Responsible for verifying email and password credentials, ensuring the user has 
verified their email address, and issuing a new refresh token upon success.
"""
from src.authentication.core.domain import UserIdentity
from src.authentication.core.ports import UserRepositoryPort
from src.authentication.core.ports import RefreshTokenRepositoryPort
from src.authentication.core.ports import PasswordHasherPort
from src.shared.core.ports.logger import LoggerPort
from typing import Protocol, Any, Generic, TypeVar
from src.authentication.core.domain.session import ClientMetadata

class UoWPort(Protocol):
    session: Any
UoWType = TypeVar("UoWType", bound=UoWPort)
class LoginLocalUserUseCase(Generic[UoWType]):
    """Handles user login with email and password."""

    def __init__(self, user_repo: UserRepositoryPort, refresh_repo: RefreshTokenRepositoryPort, hasher: PasswordHasherPort, logger: LoggerPort):
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._hasher = hasher
        self._logger = logger

    async def execute(self, uow: UoWType, email: str, password: str, client_meta: ClientMetadata | None = None) -> tuple[UserIdentity, str]:
        """
        Authenticate a user. 
        Returns (user, raw_refresh_token).
        Raises ValueError on invalid credentials or unverified email.
        """
        from src.authentication.core.domain import InvalidCredentialsException, UnverifiedEmailException
        
        user = await self._user_repo.find_by_email(uow.session, email)
        if not user:
            await self._logger.warning(f"Login failed: Email {email} not found")
            await self._hasher.dummy_verify()
            raise InvalidCredentialsException()

        # Gatekeeper: Block users who haven't proved ownership of their email.
        if not user.is_verified:
            await self._logger.warning(f"Login failed: Email {email} is not verified")
            raise UnverifiedEmailException()

        stored_hash = await self._user_repo.find_password_hash(uow.session, user.id)
        
        # Security check: If a user registered via OAuth, they won't have a local password.
        # We must prevent them from logging in locally to avoid bypassing the OAuth provider.
        if not stored_hash:
            await self._logger.warning(f"Login failed: User {user.id} has no password set (OAuth only)")
            await self._hasher.dummy_verify()
            raise InvalidCredentialsException()

        # Timing attack mitigation: We only verify the hash if it exists. 
        # (Note: For stricter timing attack prevention, a dummy hash comparison could be used when user is not found)
        if not await self._hasher.verify_password(password, stored_hash):
            await self._logger.warning(f"Login failed: Invalid password for user {user.id}")
            raise InvalidCredentialsException()

        # Restore user if soft deleted
        if user.deleted_at is not None:
            await self._user_repo.undelete_user(uow.session, user.id)
            user.deleted_at = None
            await self._logger.info(f"User {user.id} account restored on local login")

        # Issue a long-lived refresh token. The API layer will wrap this in an HttpOnly cookie.
        token = await self._refresh_repo.create(uow.session, user.id, client_meta=client_meta)
        await self._logger.info(f"User {user.id} logged in successfully via local auth")
        return user, token
