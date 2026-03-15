"""
Security tests:
- JWT token validation edge cases
- RLS isolation assertions
- Upload route auth enforcement
"""
import uuid

import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token, create_refresh_token, verify_token
from jose import JWTError


class TestJWTSecurity:
    def test_access_token_cannot_be_used_as_refresh(self) -> None:
        token = create_access_token("user-123", "test@example.com")
        with pytest.raises(JWTError):
            verify_token(token, expected_type="refresh")

    def test_refresh_token_cannot_be_used_as_access(self) -> None:
        token = create_refresh_token("user-123")
        with pytest.raises(JWTError):
            verify_token(token, expected_type="access")

    def test_tampered_token_rejected(self) -> None:
        token = create_access_token("user-123", "test@example.com")
        # Tamper with the payload section
        parts = token.split(".")
        parts[1] = parts[1] + "tampered"
        bad_token = ".".join(parts)
        with pytest.raises(JWTError):
            verify_token(bad_token)

    def test_wrong_secret_rejected(self) -> None:
        """Token signed with different secret should be rejected."""
        from jose import jwt
        payload = {"sub": "user-123", "type": "access", "jti": "test-jti"}
        bad_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        with pytest.raises(JWTError):
            verify_token(bad_token)

    def test_valid_access_token_roundtrip(self) -> None:
        user_id = str(uuid.uuid4())
        email = "roundtrip@example.com"
        token = create_access_token(user_id, email)
        payload = verify_token(token, expected_type="access")
        assert payload.sub == user_id
        assert payload.extra.get("email") == email

    def test_token_contains_jti(self) -> None:
        """Each token should have a unique JTI (JWT ID)."""
        token1 = create_access_token("user-1", "a@example.com")
        token2 = create_access_token("user-1", "a@example.com")
        p1 = verify_token(token1)
        p2 = verify_token(token2)
        assert p1.jti != p2.jti


@pytest.mark.asyncio
class TestUploadAuthEnforcement:
    async def test_voice_upload_without_auth_fails(self, client: AsyncClient) -> None:
        import io
        response = await client.post(
            "/api/upload/voice",
            files={"file": ("test.mp3", io.BytesIO(b"fake"), "audio/mpeg")},
        )
        assert response.status_code == 403  # no auth header

    async def test_photo_upload_without_auth_fails(self, client: AsyncClient) -> None:
        import io
        response = await client.post(
            "/api/upload/photos",
            files={"files": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
        )
        assert response.status_code == 403

    async def test_transcript_upload_without_auth_fails(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/upload/transcript",
            json={"transcript": "This is a test transcript with more than fifty characters."},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestRetrieveAuthEnforcement:
    async def test_website_retrieve_without_auth_fails(self, client: AsyncClient) -> None:
        fake_user_id = str(uuid.uuid4())
        response = await client.get(f"/api/retrieve/website/{fake_user_id}")
        assert response.status_code == 403

    async def test_personality_retrieve_without_auth_fails(self, client: AsyncClient) -> None:
        fake_user_id = str(uuid.uuid4())
        response = await client.get(f"/api/retrieve/personality/{fake_user_id}")
        assert response.status_code == 403

    async def test_voiceclips_retrieve_without_auth_fails(self, client: AsyncClient) -> None:
        fake_user_id = str(uuid.uuid4())
        response = await client.get(f"/api/retrieve/voiceclips/{fake_user_id}")
        assert response.status_code == 403

    async def test_qa_without_auth_fails(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/retrieve/qa",
            json={"user_id": str(uuid.uuid4()), "question": "Tell me about yourself"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestCrossUserIsolation:
    async def test_cannot_access_other_users_website(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """User A cannot fetch User B's website schema."""
        other_user_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/retrieve/website/{other_user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_cannot_access_other_users_personality(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        other_user_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/retrieve/personality/{other_user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_cannot_generate_qa_for_other_user(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        other_user_id = str(uuid.uuid4())
        response = await client.post(
            "/api/retrieve/qa",
            json={"user_id": other_user_id, "question": "Tell me about yourself"},
            headers=auth_headers,
        )
        assert response.status_code == 403
