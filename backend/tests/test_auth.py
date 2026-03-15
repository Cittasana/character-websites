"""
Tests for authentication endpoints: register, login, refresh, me.
These tests mock the Supabase auth client to avoid hitting the real service.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


def _make_supabase_auth_mock(user_id=None, fail=False, no_session=False):
    """Build a mock for the supabase-py anon client auth calls."""
    client_mock = MagicMock()

    if fail:
        client_mock.auth.sign_up.side_effect = Exception("Email already registered")
        client_mock.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        return client_mock

    uid = user_id or str(uuid.uuid4())
    user_mock = MagicMock()
    user_mock.id = uid
    user_mock.email = "test@example.com"

    session_mock = MagicMock()
    session_mock.access_token = f"access-{uid}"
    session_mock.refresh_token = f"refresh-{uid}"

    auth_response = MagicMock()
    auth_response.user = user_mock
    auth_response.session = None if no_session else session_mock

    client_mock.auth.sign_up.return_value = auth_response
    client_mock.auth.sign_in_with_password.return_value = auth_response
    client_mock.auth.refresh_session.return_value = auth_response
    client_mock.auth.get_user.return_value = auth_response

    # Table queries (for is_active check, profile row, audit logs)
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.single.return_value = query
    query.insert.return_value = query
    query.execute.return_value = MagicMock(data=[{
        "id": uid,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "subdomain": None,
        "plan": "free",
    }])
    client_mock.table.return_value = query

    return client_mock


@pytest.mark.asyncio
async def test_register_success() -> None:
    from app.main import app

    mock_client = _make_supabase_auth_mock()

    with patch("app.auth.router.get_supabase_anon", return_value=mock_client), \
         patch("app.auth.router.get_supabase", return_value=mock_client), \
         patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/auth/register",
                json={"email": "new@example.com", "password": "securepass123", "full_name": "New User"},
            )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_weak_password() -> None:
    from app.main import app

    with patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/auth/register",
                json={"email": "weak@example.com", "password": "short"},
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success() -> None:
    from app.main import app

    mock_client = _make_supabase_auth_mock()

    with patch("app.auth.router.get_supabase_anon", return_value=mock_client), \
         patch("app.auth.router.get_supabase", return_value=mock_client), \
         patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/auth/login",
                json={"email": "login@example.com", "password": "loginpass123"},
            )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_credentials() -> None:
    from app.main import app

    mock_client = _make_supabase_auth_mock(fail=True)

    with patch("app.auth.router.get_supabase_anon", return_value=mock_client), \
         patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/auth/login",
                json={"email": "wrongpw@example.com", "password": "wrongpassword"},
            )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth() -> None:
    from app.main import app

    with patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/auth/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token() -> None:
    from app.main import app

    mock_client = _make_supabase_auth_mock()

    with patch("app.auth.router.get_supabase_anon", return_value=mock_client), \
         patch("app.supabase_client.check_supabase_health", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/auth/refresh",
                json={"refresh_token": "some-refresh-token"},
            )

    assert response.status_code == 200
    assert "access_token" in response.json()
