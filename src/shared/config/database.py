"""
Loads PostgreSQL-specific configuration.
Builds the async SQLAlchemy connection string and manages connection pool settings.
"""
import re

from pydantic import field_validator

from .base import _BaseSettings


class DatabaseSettings(_BaseSettings):
    DB_ASYNC_URL: str = "sqlite+aiosqlite:///./auth.db"

    @field_validator("DB_ASYNC_URL")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        # Replaces postgres://, postgresql://, postgresql+psycopg2:// etc with postgresql+asyncpg://
        return re.sub(r"^postgres(?:ql)?(?:\+[a-zA-Z0-9_]+)?://", "postgresql+asyncpg://", v)

    CACHE_URL: str = "redis://localhost:6379/0"
