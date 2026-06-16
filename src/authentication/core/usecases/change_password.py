from typing import Protocol, Any, Generic, TypeVar
from src.authentication.core.ports import UserRepositoryPort, PasswordHasherPort
from src.shared.core.ports.logger import LoggerPort
from src.authentication.core.domain.exceptions import InvalidCredentialsException
from uuid import UUID

class UoWPort(Protocol):
    session: Any
UoWType = TypeVar("UoWType", bound=UoWPort)

class ChangePasswordUseCase(Generic[UoWType]):
    """Handles updating a user's password when they are already authenticated."""
    
    def __init__(self, user_repo: UserRepositoryPort, hasher: PasswordHasherPort, logger: LoggerPort):
        self._user_repo = user_repo
        self._hasher = hasher
        self._logger = logger

    async def execute(self, uow: UoWType, user_id: UUID, current_password: str | None, new_password: str) -> None:
        if current_password and current_password == new_password:
            from src.authentication.core.domain.exceptions import SamePasswordException
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
        
        await self._logger.info(f"User {user_id} updated their password successfully")
