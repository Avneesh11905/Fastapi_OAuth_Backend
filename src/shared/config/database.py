"""
Loads PostgreSQL-specific configuration.
Builds the async SQLAlchemy connection string and manages connection pool settings.
"""
from .base import _BaseSettings
from typing import Optional
from urllib.parse import quote_plus
from pydantic import field_validator
import re

class DatabaseSettings(_BaseSettings):
    DB_ASYNC_URL: str

    @field_validator("DB_ASYNC_URL")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        # Replaces postgres://, postgresql://, postgresql+psycopg2:// etc with postgresql+asyncpg://
        return re.sub(r"^postgres(?:ql)?(?:\+[a-zA-Z0-9_]+)?://", "postgresql+asyncpg://", v)

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_USERNAME: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        userinfo = ""
        if self.REDIS_USERNAME and self.REDIS_PASSWORD:
            userinfo = f"{quote_plus(self.REDIS_USERNAME)}:{quote_plus(self.REDIS_PASSWORD)}@"
        elif self.REDIS_PASSWORD:
            userinfo = f":{quote_plus(self.REDIS_PASSWORD)}@"
        elif self.REDIS_USERNAME:
            userinfo = f"{quote_plus(self.REDIS_USERNAME)}@"
            
        return f"redis://{userinfo}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
