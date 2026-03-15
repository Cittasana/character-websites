"""
Audio downloader — Omi cloud → local encrypted temporary buffer.

Security requirements:
- Audio is written to disk ONLY as Fernet-encrypted bytes
- Temp file is created in a controlled temp directory with restricted permissions
- After successful upload, the temp file is IMMEDIATELY deleted
- The plaintext audio bytes never persist to disk

Encryption: cryptography.fernet (symmetric, AES-128 CBC + HMAC-SHA256)
"""
import hashlib
import logging
import os
import secrets
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken

from omi.config import get_settings
from omi.sync.detector import OmiRecording

logger = logging.getLogger(__name__)

# Temp directory for encrypted buffers
_TEMP_DIR_NAME = "cw_omi_buffers"


@dataclass
class DownloadedAudio:
    """
    A downloaded audio file in an encrypted temporary buffer.
    Use as a context manager to ensure cleanup.
    """
    encrypted_path: Path        # path to the Fernet-encrypted file on disk
    sha256_hash: str            # SHA-256 of the PLAINTEXT audio (for deduplication)
    content_type: str           # MIME type of the audio
    size_bytes: int             # size of the plaintext audio
    filename: str               # suggested filename for upload
    recording_id: str           # Omi conversation ID


class AudioDownloader:
    """
    Downloads audio from Omi cloud and stores it in an encrypted temp buffer.

    Usage (as context manager — ensures cleanup):
        async with downloader.download(recording) as audio:
            # audio.encrypted_path is available here
            plaintext = downloader.decrypt(audio.encrypted_path)
            # process plaintext...
        # file is deleted after the block exits
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        settings = get_settings()
        key = encryption_key or settings.fernet_key
        if key is None:
            # Generate a session key if none configured (ephemeral — data lost on restart)
            logger.warning(
                "No TEMP_BUFFER_ENCRYPTION_KEY configured — generating ephemeral key. "
                "Set TEMP_BUFFER_ENCRYPTION_KEY in .env for production."
            )
            key = Fernet.generate_key()

        self._fernet = Fernet(key)
        self._settings = settings
        self._temp_dir = self._ensure_temp_dir()
        self._http_client: Optional[httpx.AsyncClient] = None

    def _ensure_temp_dir(self) -> Path:
        """Create the temp directory with restricted permissions (700)."""
        base = Path(tempfile.gettempdir()) / _TEMP_DIR_NAME
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        return base

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=120.0,  # large files may take time
                follow_redirects=True,
                headers={"User-Agent": "CharacterWebsites/1.0"},
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    @asynccontextmanager
    async def download(
        self,
        recording: OmiRecording,
        access_token: Optional[str] = None,
    ) -> AsyncGenerator[DownloadedAudio, None]:
        """
        Context manager: download audio from Omi, yield DownloadedAudio, then delete.

        The encrypted temp file is deleted on exit — even if an exception occurs.

        Args:
            recording: The OmiRecording to download
            access_token: Optional bearer token if the audio URL is protected
        """
        audio_url = recording.audio_url
        if not audio_url:
            raise AudioDownloadError(
                f"Recording {recording.id} has no audio URL"
            )

        encrypted_path = self._temp_dir / f"{secrets.token_hex(16)}.enc"

        try:
            # Download audio bytes
            logger.info(
                f"Downloading audio for recording {recording.id} "
                f"(duration={recording.duration_seconds}s)"
            )

            headers = {}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

            try:
                response = await self.http_client.get(audio_url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise AudioDownloadError(
                    f"HTTP {exc.response.status_code} downloading audio for {recording.id}"
                ) from exc
            except httpx.RequestError as exc:
                raise AudioDownloadError(
                    f"Network error downloading audio for {recording.id}: {exc}"
                ) from exc

            audio_bytes = response.content
            content_type = response.headers.get("content-type", "audio/wav")

            # Compute SHA-256 of plaintext (for deduplication)
            sha256_hash = hashlib.sha256(audio_bytes).hexdigest()

            # Encrypt and write to disk
            encrypted_bytes = self._fernet.encrypt(audio_bytes)

            encrypted_path.write_bytes(encrypted_bytes)
            # Restrict permissions to owner-only read/write
            encrypted_path.chmod(0o600)

            logger.info(
                f"Audio downloaded and encrypted: {len(audio_bytes)} bytes "
                f"-> {len(encrypted_bytes)} bytes encrypted, SHA256={sha256_hash[:16]}..."
            )

            # Determine filename from content-type or recording metadata
            ext = _mime_to_ext(content_type)
            filename = f"omi_{recording.id}{ext}"

            downloaded = DownloadedAudio(
                encrypted_path=encrypted_path,
                sha256_hash=sha256_hash,
                content_type=content_type.split(";")[0].strip(),
                size_bytes=len(audio_bytes),
                filename=filename,
                recording_id=recording.id,
            )

            yield downloaded

        finally:
            # Always delete the temp file
            if encrypted_path.exists():
                try:
                    encrypted_path.unlink()
                    logger.debug(f"Deleted encrypted temp file: {encrypted_path}")
                except OSError as exc:
                    logger.error(f"Failed to delete temp file {encrypted_path}: {exc}")

    def decrypt(self, encrypted_path: Path) -> bytes:
        """
        Decrypt an encrypted temp audio file.

        Returns the plaintext audio bytes.
        Raises AudioDecryptError if decryption fails.
        """
        try:
            encrypted_bytes = encrypted_path.read_bytes()
            return self._fernet.decrypt(encrypted_bytes)
        except InvalidToken as exc:
            raise AudioDecryptError(
                f"Failed to decrypt {encrypted_path}: wrong key or corrupted file"
            ) from exc
        except OSError as exc:
            raise AudioDecryptError(f"Cannot read file {encrypted_path}: {exc}") from exc

    def generate_key(self) -> bytes:
        """Generate a new Fernet key (for initial setup)."""
        return Fernet.generate_key()


def _mime_to_ext(content_type: str) -> str:
    """Map MIME type to file extension."""
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/wave": ".wav",
        "audio/m4a": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/mp4": ".m4a",
        "audio/ogg": ".ogg",
        "audio/opus": ".opus",
        "audio/webm": ".webm",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
    }
    base_type = content_type.split(";")[0].strip().lower()
    return mapping.get(base_type, ".wav")


class AudioDownloadError(Exception):
    """Raised when audio download fails."""
    pass


class AudioDecryptError(Exception):
    """Raised when audio decryption fails."""
    pass
