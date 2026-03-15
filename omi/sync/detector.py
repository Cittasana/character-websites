"""
New recording detection via Omi API polling.

Omi stores recordings as "conversations" (their terminology).
Each conversation has:
- id: unique identifier
- created_at: timestamp
- transcript: list of TranscriptSegment
- audio_url: signed URL (if recording was kept)
- source: 'phone_microphone' | 'omi_device'

We poll GET /v1/conversations?limit=50&start_timestamp=<epoch>
and return only recordings newer than our last_sync_at timestamp.

Omi also supports webhook triggers (trigger: memory_creation), but
since we're building a backend-to-backend integration, polling is simpler
and doesn't require a public webhook URL.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

from omi.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OmiRecording:
    """
    A single recording from Omi cloud (their terminology: conversation).
    """
    id: str                                 # Omi conversation ID
    created_at: datetime
    source: str                             # 'phone_microphone' | 'omi_device' | 'openglass'
    transcript_text: Optional[str]          # Full transcript text (joined segments)
    transcript_segments: list[dict]         # Raw segment list with timestamps
    audio_url: Optional[str]               # Signed download URL (may expire)
    duration_seconds: Optional[float]
    language: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "OmiRecording":
        """Parse an Omi conversation API response dict into OmiRecording."""
        # Build transcript text from segments
        segments = data.get("transcript_segments", []) or []
        transcript_text = " ".join(
            seg.get("text", "").strip()
            for seg in segments
            if seg.get("text")
        ).strip() or data.get("structured", {}).get("overview", None)

        # Parse created_at
        created_at_raw = data.get("created_at") or data.get("started_at")
        if isinstance(created_at_raw, (int, float)):
            created_at = datetime.fromtimestamp(created_at_raw, tz=timezone.utc)
        elif isinstance(created_at_raw, str):
            created_at = datetime.fromisoformat(
                created_at_raw.replace("Z", "+00:00")
            )
        else:
            created_at = datetime.now(timezone.utc)

        # Duration from start/end timestamps
        started = data.get("started_at")
        finished = data.get("finished_at")
        duration = None
        if started and finished:
            try:
                if isinstance(started, (int, float)) and isinstance(finished, (int, float)):
                    duration = float(finished) - float(started)
            except (TypeError, ValueError):
                pass

        return cls(
            id=str(data["id"]),
            created_at=created_at,
            source=data.get("source", "unknown"),
            transcript_text=transcript_text or None,
            transcript_segments=segments,
            audio_url=data.get("audio_url"),
            duration_seconds=duration,
        )


class RecordingDetector:
    """
    Polls the Omi API for new recordings since a given timestamp.

    Usage:
        detector = RecordingDetector(access_token="omi-access-token")
        new_recordings = await detector.fetch_new_recordings(
            since=last_sync_at
        )
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.settings = get_settings()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.settings.OMI_API_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "CharacterWebsites/1.0",
                },
                timeout=30.0,
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def fetch_new_recordings(
        self,
        since: Optional[datetime] = None,
        limit: int = 50,
        source_filter: Optional[str] = None,
    ) -> list[OmiRecording]:
        """
        Fetch conversations (recordings) from Omi cloud that are newer than `since`.

        Args:
            since: Only return recordings after this timestamp (None = all)
            limit: Max recordings per request
            source_filter: Filter by source ('omi_device' to get only wearable recordings)

        Returns:
            List of OmiRecording objects, sorted oldest-first
        """
        params: dict = {"limit": min(limit, self.settings.SYNC_MAX_RECORDINGS_PER_POLL)}

        if since is not None:
            # Omi API accepts start_timestamp as Unix epoch
            params["start_timestamp"] = int(since.timestamp())

        if source_filter:
            params["source"] = source_filter

        logger.info(
            f"Polling Omi API for recordings since={since.isoformat() if since else 'beginning'}"
        )

        try:
            response = await self.http_client.get("/v1/conversations", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Omi API returned {exc.response.status_code}: {exc.response.text[:200]}"
            )
            if exc.response.status_code == 401:
                raise OmiTokenExpiredError(
                    "Omi access token expired or invalid"
                ) from exc
            raise OmiAPIError(
                f"Omi API error: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Omi API request failed: {exc}")
            raise OmiAPIError(f"Network error reaching Omi API: {exc}") from exc

        raw_conversations = response.json()

        # Handle both list response and {"conversations": [...]} shape
        if isinstance(raw_conversations, dict):
            raw_conversations = raw_conversations.get("conversations", [])

        recordings = []
        for item in raw_conversations:
            try:
                recording = OmiRecording.from_api_response(item)
                # Double-check timestamp filter (API may not be precise)
                if since is not None and recording.created_at <= since:
                    continue
                recordings.append(recording)
            except (KeyError, ValueError) as exc:
                logger.warning(f"Skipping malformed conversation {item.get('id')}: {exc}")

        # Sort oldest-first so we process in order
        recordings.sort(key=lambda r: r.created_at)

        logger.info(f"Detected {len(recordings)} new recording(s)")
        return recordings

    async def get_recording_audio_url(self, conversation_id: str) -> Optional[str]:
        """
        Fetch a fresh signed audio URL for a specific conversation.
        Omi signed URLs expire; use this when the original URL in the
        conversation has expired.
        """
        try:
            response = await self.http_client.get(
                f"/v1/conversations/{conversation_id}/recording"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return data.get("url") or data.get("audio_url")
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Failed to get audio URL for {conversation_id}: {exc.response.status_code}"
            )
            return None
        except httpx.RequestError as exc:
            logger.error(f"Network error fetching audio URL: {exc}")
            return None


class OmiAPIError(Exception):
    """Raised when the Omi API returns an error."""
    pass


class OmiTokenExpiredError(OmiAPIError):
    """Raised when the Omi access token is expired or invalid."""
    pass
