"""
Lists all active sessions for a user.
"""
from typing import Protocol, Any, Generic, TypeVar
from src.authentication.core.domain.session import ActiveSession
from src.authentication.core.ports import RefreshTokenRepositoryPort
from uuid import UUID

class UoWPort(Protocol):
    session: Any
UoWType = TypeVar("UoWType", bound=UoWPort)
class ListSessionsUseCase(Generic[UoWType]):
    """Lists all active sessions for a user."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort):
        self._refresh_repo = refresh_repo

    async def execute(self, uow: UoWType, user_id: UUID, current_token: str | None = None) -> list[ActiveSession]:
        """
        Get all active devices/sessions for the user.
        """
        return await self._refresh_repo.get_active_sessions(uow.session, user_id, current_token)
