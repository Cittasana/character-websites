"""
Test fixtures and configuration.
Uses SQLite in-memory for unit tests (no real PostgreSQL required).
Integration tests require a running PostgreSQL + Redis.
"""
import asyncio
import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Override environment before any app imports
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars!")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test_key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test_secret")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/15")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/15")

from app.auth.security import create_access_token, get_password_hash
from app.database import Base
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with database override."""
    from app.database import get_db

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """JWT auth headers for the test user."""
    token = create_access_token(str(test_user.id), test_user.email)
    return {"Authorization": f"Bearer {token}"}
