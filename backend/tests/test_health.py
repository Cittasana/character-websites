"""
Tests for health check and basic API endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Health endpoint should return 200 without auth."""
    response = await client.get("/health")
    # DB may not be available in test env, but endpoint should respond
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient) -> None:
    """Verify security headers are injected by middleware."""
    response = await client.get("/health")
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "strict-transport-security" in headers
