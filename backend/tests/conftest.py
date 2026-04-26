"""
Test fixtures and configuration.
Uses mocked Supabase clients for unit tests (no live Supabase required).
Integration tests that hit the real Supabase service are opt-in via marker.
"""
import asyncio
import os
import uuid
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set required env vars before any app imports
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/15")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/15")


# ── Fake Supabase client ──────────────────────────────────────────────────────

def _make_fake_auth_user(user_id: str = None, email: str = "test@example.com"):
    """Build a minimal object that looks like a Supabase auth.User."""
    uid = user_id or str(uuid.uuid4())
    user = MagicMock()
    user.id = uid
    user.email = email
    return user


def _make_fake_supabase(user_row: dict = None):
    """Build a MagicMock that mimics the supabase-py Client API."""
    client = MagicMock()

    # Default user row returned by table("users")
    default_user = user_row or {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "username": "testuser",
        "display_name": "Test User",
        "subscription_status": "active",
        "modes_unlocked": ["cv"],
    }

    # Fluent query builder — each method returns the mock itself so chains work
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.in_.return_value = query
    query.order.return_value = query
    query.limit.return_value = query
    query.single.return_value = query
    query.insert.return_value = query
    query.update.return_value = query
    query.delete.return_value = query
    query.execute.return_value = MagicMock(data=[default_user], count=1)

    client.table.return_value = query
    client.rpc.return_value = query

    # Storage mock
    storage_bucket = MagicMock()
    storage_bucket.upload.return_value = MagicMock(path="test/path.mp3")
    storage_bucket.download.return_value = b"fake audio bytes"
    storage_bucket.create_signed_url.return_value = {"signedURL": "https://signed.example.com/file"}
    storage_bucket.remove.return_value = MagicMock()
    client.storage.from_.return_value = storage_bucket

    return client


# ── Test user setup ───────────────────────────────────────────────────────────

TEST_USER_ID = str(uuid.uuid4())
TEST_USER_EMAIL = "test@example.com"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_user_id() -> str:
    return TEST_USER_ID


@pytest.fixture(scope="function")
def test_user_email() -> str:
    return TEST_USER_EMAIL


@pytest.fixture(scope="function")
def fake_auth_user(test_user_id, test_user_email):
    return _make_fake_auth_user(test_user_id, test_user_email)


@pytest.fixture(scope="function")
def fake_supabase(test_user_id, test_user_email):
    return _make_fake_supabase({
        "id": test_user_id,
        "email": test_user_email,
        "username": "testuser",
        "display_name": "Test User",
        "subscription_status": "active",
        "modes_unlocked": ["cv"],
    })


@pytest_asyncio.fixture(scope="function")
async def client(fake_auth_user, fake_supabase) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with mocked Supabase auth and DB."""
    from app.auth.dependencies import get_current_active_user, get_current_user
    from app.main import app

    async def override_get_current_user():
        return fake_auth_user

    async def override_get_current_active_user():
        return fake_auth_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with patch("app.supabase_client.get_supabase", return_value=fake_supabase), \
         patch("app.supabase_client.get_supabase_anon", return_value=fake_supabase), \
         patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user_id) -> dict[str, str]:
    """Fake Bearer token headers (bypassed by the dependency override)."""
    return {"Authorization": f"Bearer fake-token-for-{test_user_id}"}
