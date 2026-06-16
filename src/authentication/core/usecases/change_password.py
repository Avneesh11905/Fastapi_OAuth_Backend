from uuid import UUID

from src.authentication.core.domain.exceptions import (
    InvalidCredentialsException,
    SamePasswordException,
)
from src.authentication.core.ports import (
    PasswordHasherPort,
    RefreshTokenRepositoryPort,
    UserRepositoryPort,
)
from src.shared.core.ports.logger import LoggerPort
from src.shared.core.ports.uow import UoWPort


class ChangePasswordUseCase[SessionType]:
    """Handles updating a user's password when they are already authenticated."""
    
    def __init__(self, user_repo: UserRepositoryPort[SessionType], hasher: PasswordHasherPort, logger: LoggerPort, refresh_repo: RefreshTokenRepositoryPort[SessionType]):
        self._user_repo = user_repo
        self._hasher = hasher
        self._logger = logger
        self._refresh_repo = refresh_repo

    async def execute(self, uow: UoWPort[SessionType], user_id: UUID, current_password: str | None, new_password: str) -> None:
        if current_password and current_password == new_password:
            raise SamePasswordException()
            
        stored_hash = await self._user_repo.find_password_hash(uow.session, user_id)
        
        if stored_hash:
            # User already has a local password, so they MUST provide the current one correctly
            if not current_password or not await self._hasher.verify_password(current_password, stored_hash):
                await self._logger.warning(f"Failed password change attempt for user {user_id}")
                raise InvalidCredentialsException("Incorrect current password")
                
        # Hash and update the new password
        new_hash = await self._hasher.hash_password(new_password)
        await self._user_repo.update_password(uow.session, user_id, new_hash)
        
        # Revoke all sessions
        await self._refresh_repo.revoke_all_for_user(uow.session, user_id)
        
        await self._logger.info(f"User {user_id} updated their password successfully")

