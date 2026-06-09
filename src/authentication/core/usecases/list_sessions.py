"""
Lists all active sessions for a user.
"""
from typing import Generic, TypeVar
from src.authentication.core.domain.session import ActiveSession
from src.authentication.core.ports import RefreshTokenRepositoryPort

SessionType = TypeVar("SessionType")
class ListSessionsUseCase(Generic[SessionType]):
    """Lists all active sessions for a user."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort):
        self._refresh_repo = refresh_repo

    async def execute(self, session: SessionType, user_id: str, current_token: str | None = None) -> list[ActiveSession]:
        """
        Get all active devices/sessions for the user.
        """
        return await self._refresh_repo.get_active_sessions(session, user_id, current_token)
