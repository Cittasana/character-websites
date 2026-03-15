"""
Security tests:
- Upload route auth enforcement
- Cross-user isolation (403 for other users' resources)
"""
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUploadAuthEnforcement:
    """Ensure upload routes require auth when no override is active."""

    async def test_voice_upload_without_auth_fails(self) -> None:
        """A fresh client with no auth override should reject unauthenticated requests."""
        import io
        from unittest.mock import patch

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        with patch("app.supabase_client.check_supabase_health", return_value=True):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/upload/voice",
                    files={"file": ("test.mp3", io.BytesIO(b"fake"), "audio/mpeg")},
                )
        # HTTPBearer returns 403 when Authorization header is absent
        assert response.status_code == 403

    async def test_photo_upload_without_auth_fails(self) -> None:
        import io
        from unittest.mock import patch

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        with patch("app.supabase_client.check_supabase_health", return_value=True):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/upload/photos",
                    files={"files": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
                )
        assert response.status_code == 403

    async def test_transcript_upload_without_auth_fails(self) -> None:
        from unittest.mock import patch

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        with patch("app.supabase_client.check_supabase_health", return_value=True):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/upload/transcript",
                    json={"transcript": "This is a test transcript with more than fifty characters."},
                )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestRetrieveAuthEnforcement:
    async def test_website_retrieve_without_auth_fails(self) -> None:
        from unittest.mock import patch

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        fake_user_id = str(uuid.uuid4())
        with patch("app.supabase_client.check_supabase_health", return_value=True):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(f"/api/retrieve/website/{fake_user_id}")
        assert response.status_code == 403

    async def test_personality_retrieve_without_auth_fails(self) -> None:
        from unittest.mock import patch

        from app.main import app
        from httpx import ASGITransport, AsyncClient

        fake_user_id = str(uuid.uuid4())
        with patch("app.supabase_client.check_supabase_health", return_value=True):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(f"/api/retrieve/personality/{fake_user_id}")
        assert response.status_code == 403


@pytest.mark.asyncio
class TestCrossUserIsolation:
    async def test_cannot_access_other_users_website(
        self, client: AsyncClient, auth_headers: dict, test_user_id: str
    ) -> None:
        """Authenticated user cannot fetch a different user's website schema."""
        other_user_id = str(uuid.uuid4())
        assert other_user_id != test_user_id
        response = await client.get(
            f"/api/retrieve/website/{other_user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_cannot_access_other_users_personality(
        self, client: AsyncClient, auth_headers: dict, test_user_id: str
    ) -> None:
        other_user_id = str(uuid.uuid4())
        assert other_user_id != test_user_id
        response = await client.get(
            f"/api/retrieve/personality/{other_user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_cannot_generate_qa_for_other_user(
        self, client: AsyncClient, auth_headers: dict, test_user_id: str
    ) -> None:
        other_user_id = str(uuid.uuid4())
        assert other_user_id != test_user_id
        response = await client.post(
            "/api/retrieve/qa",
            json={"user_id": other_user_id, "question": "Tell me about yourself"},
            headers=auth_headers,
        )
        assert response.status_code == 403
