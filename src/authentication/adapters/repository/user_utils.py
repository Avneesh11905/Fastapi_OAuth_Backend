"""
Shared utilities for mapping SQLAlchemy ORM models to pure Domain Entities.
Ensures that the core Use Cases only ever interact with `UserIdentity` Pydantic models,
preventing SQLAlchemy dependencies from leaking into the business logic layer.
"""
from typing import cast

from pydantic import AnyHttpUrl

from src.authentication.core.domain import UserIdentity
from src.shared.infrastructure.sql.tables import User


def to_identity(user: User) -> UserIdentity:
    """Map an ORM User to a pure domain UserIdentity."""
    return UserIdentity(
        id=user.id,
        email=user.email,
        is_verified=user.is_verified,
        name=user.name,
        picture=cast(AnyHttpUrl, user.picture) if user.picture else None,
        deleted_at=user.deleted_at,
    )
