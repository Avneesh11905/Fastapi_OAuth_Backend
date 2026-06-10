"""
Executes database queries against the User database tables using SQLAlchemy.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.authentication.core.domain import UserIdentity
from src.shared.infrastructure.sql.tables import User, UserOAuthAccount, UserPassword
from src.authentication.core.ports.repository.user import UserRepositoryPort
from .user_utils import to_identity

class SQLUserRepositoryAdapter(UserRepositoryPort[AsyncSession]):
    """Implements UserRepositoryPort using SQLAlchemy."""

    async def find_by_oauth(self, session: AsyncSession, provider: str, oauth_sub: str) -> UserIdentity | None:
        """Look up a user by their OAuth provider + subject ID."""
        result = await session.execute(
            select(UserOAuthAccount).where(
                UserOAuthAccount.provider == provider,
                UserOAuthAccount.oauth_sub == oauth_sub,
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            return None

        user_result = await session.execute(select(User).where(User.id == account.user_id))
        user = user_result.scalar_one()
        return to_identity(user)

    async def find_by_email(self, session: AsyncSession, email: str) -> UserIdentity | None:
        """Look up a user by email."""
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return to_identity(user)

    async def find_password_hash(self, session: AsyncSession, user_id: str) -> str | None:
        """Look up the password hash for a given user ID."""
        result = await session.execute(select(UserPassword).where(UserPassword.user_id == user_id))
        record = result.scalar_one_or_none()
        return record.password_hash if record else None

    async def create_user_with_oauth(
        self, session: AsyncSession, email: str, name: str | None, picture: str | None,
        provider: str, oauth_sub: str,
    ) -> UserIdentity:
        """Create a new user and link an OAuth account."""
        user = User(email=email, name=name, picture=picture, is_verified=True)
        session.add(user)
        await session.flush()

        oauth_account = UserOAuthAccount(
            user_id=user.id,
            provider=provider,
            oauth_sub=oauth_sub,
        )
        session.add(oauth_account)
        await session.flush()
        await session.refresh(user)
        return to_identity(user)

    async def link_oauth_account(
        self, session: AsyncSession, user_id: str, provider: str, oauth_sub: str,
    ) -> None:
        """Link a new OAuth provider to an existing user."""
        account = UserOAuthAccount(
            user_id=user_id,
            provider=provider,
            oauth_sub=oauth_sub,
        )
        session.add(account)

    async def create_user_with_password(
        self, session: AsyncSession, email: str, name: str | None, password_hash: str | None, is_verified: bool = False
    ) -> UserIdentity:
        """Create a new user and store their local password."""
        user = User(email=email, name=name, is_verified=is_verified)
        session.add(user)
        await session.flush()

        if password_hash is not None:
            user_password = UserPassword(user_id=user.id, password_hash=password_hash)
            session.add(user_password)
            
        await session.flush()
        await session.refresh(user)
        return to_identity(user)

    async def update_password(self, session: AsyncSession, user_id: str, password_hash: str) -> None:
        """Update or insert a password for a user."""
        result = await session.execute(select(UserPassword).where(UserPassword.user_id == user_id))
        record = result.scalar_one_or_none()
        if record:
            record.password_hash = password_hash
        else:
            record = UserPassword(user_id=user_id, password_hash=password_hash)
            session.add(record)

    async def disable_local_login(self, session: AsyncSession, user_id: str) -> None:
        """Disable local password login by deleting the user password."""
        result = await session.execute(select(UserPassword).where(UserPassword.user_id == user_id))
        record = result.scalar_one_or_none()
        if record:
            await session.delete(record)

    async def verify_user_email(self, session: AsyncSession, user_id: str) -> None:
        """Mark a user as verified."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_verified = True

    async def undelete_user(self, session: AsyncSession, user_id: str) -> None:
        """Clear the deleted_at flag to restore a soft-deleted user."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.deleted_at = None

    async def cleanup_unverified_users(self, session: AsyncSession, hours_old: int = 24) -> int:
        """Delete unverified users older than the specified hours."""
        from sqlalchemy import delete
        from datetime import datetime, timedelta, timezone
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_old)
        stmt = delete(User).where(User.is_verified.is_(False), User.created_at < cutoff)
        result = await session.execute(stmt)
        return int(result.rowcount)  # type: ignore

    async def cleanup_soft_deleted_users(self, session: AsyncSession, days_old: int = 30) -> int:
        """Permanently delete users who were soft-deleted more than `days_old` days ago."""
        from sqlalchemy import delete
        from datetime import datetime, timedelta, timezone
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        stmt = delete(User).where(User.deleted_at.is_not(None), User.deleted_at < cutoff)
        result = await session.execute(stmt)
        return int(result.rowcount)  # type: ignore
