"""
Defines the global declarative base and centralized SQLAlchemy ORM models.
Stores the schema definitions for Users, RefreshTokens, and OAuthAccounts.
Centralized here because multiple domains (Auth, Users) need to query these underlying tables.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from .connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    picture: Mapped[str | None] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    receive_updates: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    oauth_accounts: Mapped[list["UserOAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    password: Mapped[Optional["UserPassword"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin", uselist=False
    )



class UserOAuthAccount(Base):
    """One row per OAuth provider per user — enables multi-provider account linking."""
    __tablename__ = "user_oauth_accounts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    oauth_sub: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("provider", "oauth_sub", name="uq_provider_oauth_sub"),
    )

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")


class UserPassword(Base):
    """Stores local authentication credentials (hashed passwords)."""
    __tablename__ = "user_passwords"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="password")



class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[UUID] = mapped_column(Uuid, default=uuid7, index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_provider: Mapped[str] = mapped_column(String, nullable=False, server_default="local")
    
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_active_sessions", "user_id", "used", "expires_at"),
    )


class SystemLog(Base):
    __tablename__ = "system_logs"   

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    level: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, index=True)
    message: Mapped[str] = mapped_column(String)
    file: Mapped[str | None] = mapped_column(String, nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
