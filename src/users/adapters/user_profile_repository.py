"""
Executes database queries for user profiles using SQLAlchemy.
Maps raw database rows into pure `UserProfile` domain entities to prevent ORM leakage.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.users.core.domain import UserProfile
from src.shared.infrastructure.sql.tables import User

class SQLUserProfileRepository:
    """Implements UserProfileRepositoryPort using SQLAlchemy."""

    def _to_profile(self, user: User) -> UserProfile:
        methods = []
        if user.password:
            methods.append("local")
        for account in user.oauth_accounts:
            methods.append(account.provider)
            
        return UserProfile(
            id=str(user.id),
            email=user.email,
            name=user.name,
            picture=user.picture,
            receive_updates=user.receive_updates,
            login_methods=methods
        )

    async def get_profile(self, session: AsyncSession, user_id: str) -> UserProfile | None:
        result = await session.execute(select(User).options(selectinload(User.oauth_accounts)).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return self._to_profile(user)

    async def update_profile(
        self, session: AsyncSession, user_id: str, name: str | None, picture: str | None, receive_updates: bool
    ) -> UserProfile:
        result = await session.execute(select(User).options(selectinload(User.oauth_accounts)).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            from src.users.core.domain.exceptions import UserNotFoundException
            raise UserNotFoundException()
        user.name = name
        user.picture = picture
        user.receive_updates = receive_updates
        await session.flush()
        return self._to_profile(user)

    async def delete_user(self, session: AsyncSession, user_id: str) -> None:
        """Soft delete a user."""
        from datetime import datetime, timezone
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.deleted_at = datetime.now(timezone.utc)
            await session.flush()
