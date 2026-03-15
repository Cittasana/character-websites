"""
Tests for authentication endpoints: register, login, refresh, me.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "password": "securepass123", "full_name": "New User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    # Register once
    await client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "securepass123"},
    )
    # Register again with same email
    response = await client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "anotherpass456"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    # Register first
    await client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "loginpass123"},
    )
    # Login
    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "loginpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "wrongpw@example.com", "password": "correctpass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient) -> None:
    # Register + login
    await client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "password": "mepassword123"},
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "me@example.com", "password": "mepassword123"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "refresh@example.com", "password": "refreshpass123"},
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "refresh@example.com", "password": "refreshpass123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient) -> None:
    """Access tokens should NOT be accepted as refresh tokens."""
    await client.post(
        "/api/auth/register",
        json={"email": "badrefresh@example.com", "password": "badpass123"},
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "badrefresh@example.com", "password": "badpass123"},
    )
    access_token = login_resp.json()["access_token"]  # wrong token type

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401
