"""
Manages the global SQLAlchemy asynchronous engine and session maker.
Provides the `get_db` dependency used to inject database sessions into the API routes.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.shared.config import database_settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base for all ORM models."""


engine = create_async_engine(
    database_settings.DB_ASYNC_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
