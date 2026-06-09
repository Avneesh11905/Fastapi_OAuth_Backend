"""
Revokes a specific session (device logout).
"""
from typing import Generic, TypeVar
from src.authentication.core.ports import RefreshTokenRepositoryPort

SessionType = TypeVar("SessionType")
class RevokeSessionUseCase(Generic[SessionType]):
    """Revokes a specific session family, logging out that device."""
    
    def __init__(self, refresh_repo: RefreshTokenRepositoryPort):
        self._refresh_repo = refresh_repo

    async def execute(self, session: SessionType, user_id: str, family_id: str) -> None:
        """
        Revokes a session by family_id.
        Verifies that the session actually belongs to the user to prevent IDOR.
        """
        # Fetch active sessions to verify ownership
        sessions = await self._refresh_repo.get_active_sessions(session, user_id)
        if not any(s.family_id == family_id for s in sessions):
            from src.authentication.core.domain.exceptions import SessionNotFoundException
            raise SessionNotFoundException()
            
        await self._refresh_repo.revoke_by_family(session, family_id)
