"""
Recording deduplication — prevents double-uploading the same audio file.

Strategy:
1. Before uploading, compute SHA-256 of the plaintext audio
2. Check if that hash already exists in our backend `recordings` table
3. Also check if the Omi conversation_id was already synced (stored in recording metadata)
4. Only proceed with upload if neither check finds a match

The backend API exposes a deduplication check endpoint:
  GET /api/upload/voice/check-duplicate?sha256=<hash>&omi_id=<conversation_id>
  Returns: {exists: bool, recording_id?: string}
"""
import logging
from typing import Optional

import httpx

from omi.config import get_settings

logger = logging.getLogger(__name__)


class RecordingDeduplicator:
    """
    Checks whether a recording (by SHA-256 hash or Omi conversation ID) has
    already been uploaded.

    This class hits the backend API — it does NOT query the DB directly.
    """

    def __init__(self, user_jwt: str):
        self.user_jwt = user_jwt
        self.settings = get_settings()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.settings.BACKEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.user_jwt}",
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def is_duplicate(
        self,
        sha256_hash: str,
        omi_conversation_id: Optional[str] = None,
    ) -> bool:
        """
        Check if this recording already exists in the backend.

        Checks both:
        - SHA-256 hash of the audio file
        - Omi conversation_id (stored in recording metadata)

        Returns True if duplicate (skip upload), False if new (proceed).
        """
        params: dict = {"sha256": sha256_hash}
        if omi_conversation_id:
            params["omi_id"] = omi_conversation_id

        try:
            response = await self.http_client.get(
                "/api/upload/voice/check-duplicate",
                params=params,
            )
            if response.status_code == 404:
                # Endpoint not yet implemented — fall back to False (allow upload)
                logger.warning(
                    "Deduplication endpoint not found — proceeding with upload. "
                    "Implement GET /api/upload/voice/check-duplicate in Backend Phase 2."
                )
                return False
            response.raise_for_status()
            data = response.json()
            is_dup = bool(data.get("exists", False))
            if is_dup:
                logger.info(
                    f"Duplicate detected: sha256={sha256_hash[:16]}... "
                    f"omi_id={omi_conversation_id} -> recording_id={data.get('recording_id')}"
                )
            return is_dup

        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Deduplication check failed: {exc.response.status_code} {exc.response.text[:100]}"
            )
            # On error, allow upload (fail-open — better to double-upload than to skip)
            return False
        except httpx.RequestError as exc:
            logger.error(f"Network error during deduplication check: {exc}")
            return False

    def compute_sha256(self, audio_bytes: bytes) -> str:
        """
        Compute SHA-256 hash of audio bytes.
        This is the canonical hash used for deduplication.
        """
        import hashlib
        return hashlib.sha256(audio_bytes).hexdigest()
