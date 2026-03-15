"""
Audio uploader — sends audio files to the backend POST /api/upload/voice endpoint.

Upload payload (multipart/form-data):
  - file: audio bytes
  - transcript: (optional) transcript text
  - transcript_source: 'omi' | 'whisper' | None
  - omi_conversation_id: Omi's conversation ID for deduplication
  - sha256_hash: pre-computed hash for server-side dedup
  - language: (optional) detected language code
  - duration_seconds: (optional)

JWT auth: Bearer token in Authorization header (the user's JWT from our backend).
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from omi.config import get_settings
from omi.sync.downloader import AudioDownloader, DownloadedAudio

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of a successful upload."""
    recording_id: str               # backend recording UUID
    status: str                     # 'pending' | 'processing' | 'completed'
    celery_task_id: Optional[str]   # Celery task ID for tracking analysis progress


class AudioUploader:
    """
    Uploads decrypted audio to the Character-Websites backend API.

    Security:
    - Audio is decrypted IN MEMORY (never re-written to disk as plaintext)
    - Uploaded immediately over HTTPS
    - Temp encrypted file is already deleted by AudioDownloader context manager
    """

    def __init__(self, user_jwt: str, downloader: Optional[AudioDownloader] = None):
        self.user_jwt = user_jwt
        self.settings = get_settings()
        self._downloader = downloader or AudioDownloader()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.settings.BACKEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.user_jwt}",
                },
                timeout=120.0,  # audio uploads can be large
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def upload_from_buffer(
        self,
        downloaded: DownloadedAudio,
        transcript: Optional[str] = None,
        transcript_source: Optional[str] = None,
        language: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> UploadResult:
        """
        Upload a downloaded (encrypted) audio file to the backend.

        Decrypts the audio in memory, then posts to /api/upload/voice.
        The encrypted temp file is expected to still exist on disk.

        Args:
            downloaded: DownloadedAudio from the downloader context manager
            transcript: Optional transcript text (from Omi or Whisper)
            transcript_source: 'omi' | 'whisper' | None
            language: ISO 639-1 language code (e.g. 'en', 'de')
            duration_seconds: Audio duration

        Returns:
            UploadResult with the backend recording ID

        Raises:
            UploadError on failure
        """
        # Decrypt audio in memory
        try:
            audio_bytes = self._downloader.decrypt(downloaded.encrypted_path)
        except Exception as exc:
            raise UploadError(
                f"Failed to decrypt audio for recording {downloaded.recording_id}: {exc}"
            ) from exc

        # Build multipart form data
        files = {
            "file": (downloaded.filename, audio_bytes, downloaded.content_type),
        }

        data: dict = {
            "sha256_hash": downloaded.sha256_hash,
            "omi_conversation_id": downloaded.recording_id,
            "source": "omi",
        }

        if transcript:
            data["transcript"] = transcript
        if transcript_source:
            data["transcript_source"] = transcript_source
        if language:
            data["language"] = language
        if duration_seconds is not None:
            data["duration_seconds"] = str(duration_seconds)
        if downloaded.size_bytes:
            data["file_size_bytes"] = str(downloaded.size_bytes)

        logger.info(
            f"Uploading recording {downloaded.recording_id} "
            f"({downloaded.size_bytes} bytes, {downloaded.content_type})"
        )

        try:
            response = await self.http_client.post(
                self.settings.BACKEND_UPLOAD_VOICE_ENDPOINT,
                files=files,
                data=data,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:300]
            logger.error(f"Upload failed: HTTP {status} — {body}")

            if status == 409:
                # Duplicate detected by backend
                raise DuplicateRecordingError(
                    f"Backend rejected duplicate: {body}"
                ) from exc
            if status == 401:
                raise UploadAuthError("JWT token rejected by backend") from exc
            raise UploadError(f"Upload failed with HTTP {status}: {body}") from exc
        except httpx.RequestError as exc:
            raise UploadNetworkError(
                f"Network error uploading recording {downloaded.recording_id}: {exc}"
            ) from exc

        result_data = response.json()
        logger.info(
            f"Upload successful: recording_id={result_data.get('id')} "
            f"task_id={result_data.get('celery_task_id')}"
        )

        return UploadResult(
            recording_id=str(result_data.get("id", "")),
            status=result_data.get("processing_status", "pending"),
            celery_task_id=result_data.get("celery_task_id"),
        )

    async def upload_from_path(
        self,
        audio_path: Path,
        recording_id: str,
        content_type: str = "audio/wav",
        transcript: Optional[str] = None,
        transcript_source: Optional[str] = None,
        language: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> UploadResult:
        """
        Upload an audio file directly from a plaintext file path.
        Used for queue retries where we have the raw audio bytes.

        Note: This method expects PLAINTEXT audio (not encrypted).
        """
        import hashlib

        audio_bytes = audio_path.read_bytes()
        sha256_hash = hashlib.sha256(audio_bytes).hexdigest()

        files = {
            "file": (audio_path.name, audio_bytes, content_type),
        }
        data: dict = {
            "sha256_hash": sha256_hash,
            "omi_conversation_id": recording_id,
            "source": "omi",
        }

        if transcript:
            data["transcript"] = transcript
        if transcript_source:
            data["transcript_source"] = transcript_source
        if language:
            data["language"] = language
        if duration_seconds is not None:
            data["duration_seconds"] = str(duration_seconds)

        logger.info(f"Uploading from path: {audio_path.name} ({len(audio_bytes)} bytes)")

        try:
            response = await self.http_client.post(
                self.settings.BACKEND_UPLOAD_VOICE_ENDPOINT,
                files=files,
                data=data,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 409:
                raise DuplicateRecordingError("Duplicate rejected by backend") from exc
            raise UploadError(f"Upload from path failed: HTTP {status}") from exc
        except httpx.RequestError as exc:
            raise UploadNetworkError(f"Network error: {exc}") from exc

        result_data = response.json()
        return UploadResult(
            recording_id=str(result_data.get("id", "")),
            status=result_data.get("processing_status", "pending"),
            celery_task_id=result_data.get("celery_task_id"),
        )


class UploadError(Exception):
    """Base class for upload errors."""
    pass


class UploadNetworkError(UploadError):
    """Network error during upload (eligible for retry)."""
    pass


class UploadAuthError(UploadError):
    """JWT auth rejected — not retryable without token refresh."""
    pass


class DuplicateRecordingError(UploadError):
    """Backend rejected upload as duplicate — not retryable."""
    pass
