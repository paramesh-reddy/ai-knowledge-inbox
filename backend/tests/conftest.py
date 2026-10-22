"""Pytest configuration and isolated async test fixtures."""
import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["UPLOAD_DIR"] = "/tmp/test_uploads"
os.environ["GEMINI_API_KEY"] = ""

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
settings.gemini_api_key = None
from app.db.session import Base, get_db
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def test_env():
    """Creates an isolated SQLite database file per test."""
    db_id = uuid.uuid4().hex
    db_path = f"/tmp/test_db_{db_id}.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    yield {"engine": engine, "session_maker": session_maker, "db_path": db_path}

    await engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest_asyncio.fixture(scope="function")
async def db_session(test_env) -> AsyncGenerator[AsyncSession, None]:
    session_maker = test_env["session_maker"]
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_env) -> AsyncGenerator[AsyncClient, None]:
    session_maker = test_env["session_maker"]

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
