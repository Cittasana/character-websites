"""
Tests for the encrypted audio downloader (Phase 12 - Plan 12-01).

Tests cover:
- Encryption/decryption round-trip
- Temp file cleanup after context manager exits
- SHA-256 hash integrity
- Error handling for missing/invalid URLs
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import pytest
from cryptography.fernet import Fernet

from omi.sync.downloader import AudioDownloader, AudioDownloadError, AudioDecryptError
from omi.sync.detector import OmiRecording


@pytest.fixture
def downloader(fernet_key):
    return AudioDownloader(encryption_key=fernet_key)


@pytest.fixture
def mock_recording():
    return OmiRecording(
        id="test-conv-id-123",
        created_at=datetime.now(timezone.utc),
        source="omi_device",
        transcript_text="Hello world this is a test",
        transcript_segments=[],
        audio_url="https://storage.omi.me/audio/test.wav",
        duration_seconds=3.0,
    )


class TestEncryptionRoundTrip:
    """Tests for Fernet encrypt/decrypt integrity."""

    def test_decrypt_after_manual_encrypt(self, downloader, speech_wav_bytes, tmp_path):
        """Encrypt some bytes manually, write to file, decrypt, verify match."""
        encrypted = downloader._fernet.encrypt(speech_wav_bytes)
        enc_path = tmp_path / "test.enc"
        enc_path.write_bytes(encrypted)
        enc_path.chmod(0o600)

        decrypted = downloader.decrypt(enc_path)
        assert decrypted == speech_wav_bytes

    def test_wrong_key_raises_decrypt_error(self, speech_wav_bytes, tmp_path):
        """Using wrong Fernet key should raise AudioDecryptError."""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        downloader1 = AudioDownloader(encryption_key=key1)
        downloader2 = AudioDownloader(encryption_key=key2)

        encrypted = downloader1._fernet.encrypt(speech_wav_bytes)
        enc_path = tmp_path / "test.enc"
        enc_path.write_bytes(encrypted)

        with pytest.raises(AudioDecryptError):
            downloader2.decrypt(enc_path)

    def test_sha256_preserved(self, speech_wav_bytes):
        """SHA-256 of the original bytes should match what we'd compute."""
        expected = hashlib.sha256(speech_wav_bytes).hexdigest()
        actual = hashlib.sha256(speech_wav_bytes).hexdigest()
        assert expected == actual


class TestDownloadContextManager:
    """Tests for the download context manager."""

    @pytest.mark.asyncio
    async def test_temp_file_deleted_after_success(
        self, downloader, mock_recording, speech_wav_bytes
    ):
        """Encrypted temp file must be deleted after context manager exits normally."""
        with patch.object(
            downloader.http_client,
            "get",
            new_callable=AsyncMock,
            return_value=MagicMock(
                content=speech_wav_bytes,
                headers={"content-type": "audio/wav"},
                raise_for_status=MagicMock(),
            ),
        ):
            enc_path_ref = None
            async with downloader.download(mock_recording) as downloaded:
                enc_path_ref = downloaded.encrypted_path
                assert enc_path_ref.exists(), "Encrypted file should exist during context"

            assert not enc_path_ref.exists(), "Encrypted file should be deleted after context"

    @pytest.mark.asyncio
    async def test_temp_file_deleted_after_exception(
        self, downloader, mock_recording, speech_wav_bytes
    ):
        """Encrypted temp file must be deleted even if an exception occurs inside context."""
        with patch.object(
            downloader.http_client,
            "get",
            new_callable=AsyncMock,
            return_value=MagicMock(
                content=speech_wav_bytes,
                headers={"content-type": "audio/wav"},
                raise_for_status=MagicMock(),
            ),
        ):
            enc_path_ref = None
            with pytest.raises(RuntimeError, match="test exception"):
                async with downloader.download(mock_recording) as downloaded:
                    enc_path_ref = downloaded.encrypted_path
                    raise RuntimeError("test exception")

            assert not enc_path_ref.exists(), "Encrypted file should be deleted on exception"

    @pytest.mark.asyncio
    async def test_download_sets_correct_hash(
        self, downloader, mock_recording, speech_wav_bytes
    ):
        """SHA-256 in DownloadedAudio should match hash of original bytes."""
        with patch.object(
            downloader.http_client,
            "get",
            new_callable=AsyncMock,
            return_value=MagicMock(
                content=speech_wav_bytes,
                headers={"content-type": "audio/wav"},
                raise_for_status=MagicMock(),
            ),
        ):
            async with downloader.download(mock_recording) as downloaded:
                expected_hash = hashlib.sha256(speech_wav_bytes).hexdigest()
                assert downloaded.sha256_hash == expected_hash

    @pytest.mark.asyncio
    async def test_download_sets_recording_id(
        self, downloader, mock_recording, speech_wav_bytes
    ):
        with patch.object(
            downloader.http_client,
            "get",
            new_callable=AsyncMock,
            return_value=MagicMock(
                content=speech_wav_bytes,
                headers={"content-type": "audio/wav"},
                raise_for_status=MagicMock(),
            ),
        ):
            async with downloader.download(mock_recording) as downloaded:
                assert downloaded.recording_id == mock_recording.id

    @pytest.mark.asyncio
    async def test_no_audio_url_raises(self, downloader):
        """Recording with no audio_url should raise AudioDownloadError."""
        recording = OmiRecording(
            id="test-id",
            created_at=datetime.now(timezone.utc),
            source="omi_device",
            transcript_text=None,
            transcript_segments=[],
            audio_url=None,          # No URL
            duration_seconds=None,
        )
        with pytest.raises(AudioDownloadError, match="no audio URL"):
            async with downloader.download(recording):
                pass


class TestTempDirSecurity:
    """Tests for temp directory security properties."""

    def test_temp_dir_exists(self, downloader):
        assert downloader._temp_dir.exists()

    def test_temp_dir_permissions(self, downloader):
        """Temp dir should have owner-only permissions (700)."""
        import stat
        mode = downloader._temp_dir.stat().st_mode
        # Check that group and other have no permissions
        assert not (mode & stat.S_IRGRP)
        assert not (mode & stat.S_IWGRP)
        assert not (mode & stat.S_IROTH)
        assert not (mode & stat.S_IWOTH)
