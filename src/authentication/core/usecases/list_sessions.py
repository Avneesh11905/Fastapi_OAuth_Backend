"""
Lists all active sessions for a user.
"""

from uuid import UUID

from src.authentication.core.domain.session import ActiveSession
from src.authentication.core.ports import RefreshTokenRepositoryPort
from src.shared.core.ports.uow import UoWPort


class ListSessionsUseCase[SessionType]:
    """Lists all active sessions for a user."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort[SessionType]):
        self._refresh_repo = refresh_repo

    async def execute(self, uow: UoWPort[SessionType], user_id: UUID, current_token: str | None = None) -> list[ActiveSession]:
        """
        Get all active devices/sessions for the user.
        """
        return await self._refresh_repo.get_active_sessions(uow.session, user_id, current_token)

