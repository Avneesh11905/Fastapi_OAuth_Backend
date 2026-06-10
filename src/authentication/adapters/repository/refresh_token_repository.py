"""
Handles reading and writing Refresh Tokens.
"""
from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID
from uuid6 import uuid7
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.authentication.core.domain import UserIdentity
from src.shared.infrastructure.sql.tables import RefreshToken, User
from .refresh_token_utils import hash_token, cache_key
from src.authentication.core.ports.repository.refresh_token import RefreshTokenRepositoryPort
from src.authentication.core.domain.session import ClientMetadata, ActiveSession
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.authentication.core.ports import CachePort

class DBRefreshTokenRepositoryAdapter(RefreshTokenRepositoryPort[AsyncSession]):
    """Implements RefreshTokenRepositoryPort using SQL database."""

    def __init__(self, lifetime_days: int, cache: "CachePort | None" = None):
        self._lifetime_days = lifetime_days
        self._cache = cache

    async def create(self, session: AsyncSession, user_id: str, family_id: UUID | None = None, auth_provider: str = "local", client_meta: ClientMetadata | None = None) -> str:
        """Create a new refresh token. Returns the raw token."""
        raw_token = secrets.token_urlsafe(64)
        hashed = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self._lifetime_days)

        ip_addr = client_meta.ip_address if client_meta else None
        u_agent = client_meta.user_agent if client_meta else None

        refresh = RefreshToken(
            token=hashed,
            user_id=user_id,
            family_id=family_id or uuid7(),
            expires_at=expires_at,
            ip_address=ip_addr,
            user_agent=u_agent,
            auth_provider=auth_provider,
        )
        session.add(refresh)
        await session.flush()
        return raw_token

    async def _revoke_family(self, session: AsyncSession, family_id: UUID) -> None:
        """Revoke all tokens in a family."""
        result = await session.execute(select(RefreshToken).where(RefreshToken.family_id == family_id))
        for row in result.scalars():
            if self._cache:
                await self._cache.delete_key(cache_key(row.token))
            await session.delete(row)
            
        if self._cache:
            await self._cache.set_string(f"blacklist:family:{family_id}", "revoked", ttl=900)

    async def revoke(self, session: AsyncSession, token: str) -> None:
        """Revoke a refresh token and its entire rotation family."""
        hashed = hash_token(token)
        result = await session.execute(select(RefreshToken).where(RefreshToken.token == hashed))
        refresh = result.scalar_one_or_none()
        if refresh:
            await self._revoke_family(session, refresh.family_id)

    async def revoke_by_family(self, session: AsyncSession, family_id: str) -> None:
        """Revoke a specific token family."""
        await self._revoke_family(session, UUID(family_id))

    async def cleanup_expired(self, session: AsyncSession) -> int:
        """Delete all expired and used refresh tokens. Returns count deleted."""
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(RefreshToken).where(
                (RefreshToken.expires_at < now) | (RefreshToken.used.is_(True))
            )
        )
        token_list = result.scalars().all()
        for t in token_list:
            if self._cache:
                await self._cache.delete_key(cache_key(t.token))
            await session.delete(t)
        return len(token_list)

    async def validate(self, session: AsyncSession, token: str, client_meta: ClientMetadata | None = None) -> tuple[UserIdentity | None, str | None, str | None]:
        hashed = hash_token(token)

        result = await session.execute(select(RefreshToken).where(RefreshToken.token == hashed))
        refresh = result.scalar_one_or_none()

        if not refresh:
            return None, None, None

        now = datetime.now(timezone.utc)

        if refresh.used:
            await self._revoke_family(session, refresh.family_id)
            return None, None, None

        if refresh.expires_at < now:
            await session.delete(refresh)
            return None, None, None

        if client_meta:
            refresh.ip_address = client_meta.ip_address or refresh.ip_address
            refresh.user_agent = client_meta.user_agent or refresh.user_agent
            session.add(refresh)

        user_result = await session.execute(select(User).where(User.id == refresh.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return None, None, None

        user_identity = UserIdentity(
            id=str(user.id),
            email=user.email,
            name=user.name,
            picture=user.picture,
            is_verified=user.is_verified,
        )

        total_lifetime = timedelta(days=self._lifetime_days)
        time_remaining = refresh.expires_at - now
        threshold = total_lifetime * 0.3

        new_token = None
        if time_remaining <= threshold:
            refresh.used = True
            session.add(refresh)
            await session.flush()

            if self._cache:
                await self._cache.delete_key(cache_key(hashed))
            new_token = await self.create(session, str(user.id), family_id=refresh.family_id, auth_provider=refresh.auth_provider, client_meta=client_meta)

        return user_identity, new_token, str(refresh.family_id)

    async def get_active_sessions(self, session: AsyncSession, user_id: str, current_token: str | None = None) -> list[ActiveSession]:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.used.is_(False))
            .where(RefreshToken.expires_at > now)
        )
        sessions = []
        hashed_current = hash_token(current_token) if current_token else None
        for row in result.scalars():
            is_current = row.token == hashed_current
            sessions.append(
                ActiveSession(
                    family_id=str(row.family_id),
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    created_at=row.created_at,
                    last_active=row.updated_at,
                    is_current=is_current,
                    auth_provider=row.auth_provider,
                )
            )
        return sessions
