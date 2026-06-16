"""
Completes the password reset lifecycle.
Takes a secure UUID token generated during the 'Request Reset' phase.
If the token is valid in the ephemeral cache (Redis), it hashes the new password,
commits it to the database, and immediately invalidates the token to prevent reuse.
"""
from src.shared.core.ports.uow import UoWPort
from uuid import UUID

from src.authentication.core.ports import RefreshTokenRepositoryPort, UserRepositoryPort
from src.authentication.core.ports.security.password_hasher import PasswordHasherPort
from src.shared.core.ports.cache import CachePort


class ExecutePasswordResetUseCase[SessionType]:
    """Handles validating the token and updating the password."""
    
    def __init__(self, user_repo: UserRepositoryPort, cache: CachePort, hasher: PasswordHasherPort, refresh_repo: RefreshTokenRepositoryPort):
        self.user_repo = user_repo
        self.cache = cache
        self.hasher = hasher
        self.refresh_repo = refresh_repo
        
    async def execute(self, uow: UoWPort[SessionType], token: str, new_password: str) -> bool:
        user_id = await self.cache.get_string(f"pwd_reset:{token}")
        if not user_id:
            return False
            
        hashed_password = await self.hasher.hash_password(new_password)
        user_id_uuid = UUID(user_id)
        await self.user_repo.update_password(uow.session, user_id_uuid, hashed_password)
        
        # Invalidate all active sessions for the user
        await self.refresh_repo.revoke_all_for_user(uow.session, user_id_uuid)
        
        # Invalidate the token
        await self.cache.delete_key(f"pwd_reset:{token}")
        return True
