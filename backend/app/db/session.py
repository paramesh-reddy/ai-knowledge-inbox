"""Database session and engine setup with dual SQLite and PostgreSQL support."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import logger


class Base(DeclarativeBase):
    pass


# Choose appropriate connect_args based on DB dialect
connect_args = {}
if not settings.is_postgres:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initializes tables and extensions."""
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        if settings.is_postgres:
            try:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("PostgreSQL pgvector extension verified.")
            except Exception as e:
                logger.warning(f"Could not initialize pgvector extension: {e}")

        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
