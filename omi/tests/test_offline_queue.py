"""
Tests for offline queue (Phase 12 - Plan 12-04).

Tests cover:
- Enqueue and list
- Exponential backoff retry scheduling
- Mark succeeded (removes entry)
- Mark failed (increments count, updates next_retry_at)
- Queue full error
- Stale entry cleanup
- Per-user filtering
"""
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

import pytest

from omi.sync.queue import OfflineQueue, QueuedRecording, QueueFullError


@pytest.fixture
def queue(tmp_path, monkeypatch):
    """Fresh queue in a temp directory."""
    monkeypatch.setenv("OFFLINE_QUEUE_PATH", str(tmp_path / "queue"))
    # Reload settings cache
    from omi.config import get_settings
    get_settings.cache_clear()
    q = OfflineQueue()
    yield q
    get_settings.cache_clear()


@pytest.fixture
def fake_audio_file(tmp_path):
    """Create a fake encrypted audio file for queue entries."""
    f = tmp_path / "test_audio.enc"
    f.write_bytes(b"fake encrypted content")
    return str(f)


class TestEnqueueAndList:
    def test_enqueue_creates_entry(self, queue, fake_audio_file, mock_user_id):
        entry = queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-id-1",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="a" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=1024,
        )
        assert entry.queue_id
        assert entry.user_id == mock_user_id
        assert entry.omi_recording_id == "omi-id-1"

    def test_list_pending_returns_entry(self, queue, fake_audio_file, mock_user_id):
        queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-id-2",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="b" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=512,
        )
        pending = queue.list_pending(user_id=mock_user_id)
        assert len(pending) == 1
        assert pending[0].omi_recording_id == "omi-id-2"

    def test_enqueue_multiple(self, queue, fake_audio_file, mock_user_id):
        for i in range(3):
            queue.enqueue(
                user_id=mock_user_id,
                omi_recording_id=f"omi-id-{i}",
                encrypted_audio_path=fake_audio_file,
                sha256_hash=str(i).zfill(64),
                content_type="audio/wav",
                filename=f"test_{i}.wav",
                size_bytes=1000 * i,
            )
        pending = queue.list_pending(user_id=mock_user_id)
        assert len(pending) == 3

    def test_queue_size(self, queue, fake_audio_file, mock_user_id):
        queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-id-size",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="c" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=100,
        )
        assert queue.queue_size(user_id=mock_user_id) == 1

    def test_user_isolation(self, queue, fake_audio_file):
        user1 = "user-1-uuid"
        user2 = "user-2-uuid"
        queue.enqueue(user1, "omi-1", fake_audio_file, "a" * 64, "audio/wav", "a.wav", 100)
        queue.enqueue(user2, "omi-2", fake_audio_file, "b" * 64, "audio/wav", "b.wav", 100)

        assert queue.queue_size(user_id=user1) == 1
        assert queue.queue_size(user_id=user2) == 1


class TestMarkSucceeded:
    def test_mark_succeeded_removes_entry(self, queue, fake_audio_file, mock_user_id):
        entry = queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-success",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="d" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=200,
        )
        result = queue.mark_succeeded(entry.queue_id)
        assert result is True
        assert queue.queue_size(user_id=mock_user_id) == 0

    def test_mark_succeeded_nonexistent(self, queue):
        result = queue.mark_succeeded("nonexistent-id")
        assert result is False


class TestMarkFailed:
    def test_mark_failed_increments_retry_count(
        self, queue, fake_audio_file, mock_user_id, monkeypatch
    ):
        monkeypatch.setenv("SYNC_RETRY_MAX_ATTEMPTS", "5")
        entry = queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-fail",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="e" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=300,
        )
        updated = queue.mark_failed(entry.queue_id, error_message="test error", max_retries=5)
        assert updated is not None
        assert updated.retry_count == 1
        assert updated.error_message == "test error"
        assert updated.next_retry_at is not None

    def test_mark_failed_max_retries_removes_entry(
        self, queue, fake_audio_file, mock_user_id
    ):
        entry = queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-maxfail",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="f" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=400,
        )
        # Exhaust retries
        result = None
        for _ in range(5):
            result = queue.mark_failed(entry.queue_id, max_retries=3)
            if result is None:
                break

        assert queue.queue_size(user_id=mock_user_id) == 0

    def test_exponential_backoff_delay_increases(
        self, queue, fake_audio_file, mock_user_id
    ):
        """Each failure should increase the delay."""
        entry = queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-backoff",
            encrypted_audio_path=fake_audio_file,
            sha256_hash="g" * 64,
            content_type="audio/wav",
            filename="test.wav",
            size_bytes=500,
        )
        retry_times = []
        for i in range(3):
            updated = queue.mark_failed(entry.queue_id, max_retries=10)
            if updated:
                entry = updated
                retry_times.append(
                    datetime.fromisoformat(updated.next_retry_at)
                )

        # Each next_retry_at should be later than the previous
        assert len(retry_times) >= 2
        for i in range(1, len(retry_times)):
            assert retry_times[i] > retry_times[i - 1]


class TestQueueFull:
    def test_queue_full_error(self, queue, fake_audio_file, mock_user_id):
        """When list_pending returns max entries, enqueue should raise QueueFullError."""
        # Mock list_pending to return 500 items (the default max)
        mock_entries = [MagicMock() for _ in range(500)]
        with patch.object(queue, 'list_pending', return_value=mock_entries):
            with pytest.raises(QueueFullError):
                queue.enqueue(
                    user_id=mock_user_id,
                    omi_recording_id="omi-overflow",
                    encrypted_audio_path=fake_audio_file,
                    sha256_hash="h" * 64,
                    content_type="audio/wav",
                    filename="overflow.wav",
                    size_bytes=100,
                )


class TestStaleEntryCleanup:
    def test_missing_audio_file_cleaned_up(self, queue, tmp_path, mock_user_id):
        """An entry pointing to a non-existent audio file should be removed from list."""
        missing_path = str(tmp_path / "doesnt_exist.enc")
        entry = queue.enqueue(
            user_id=mock_user_id,
            omi_recording_id="omi-stale",
            encrypted_audio_path=missing_path,
            sha256_hash="h" * 64,
            content_type="audio/wav",
            filename="stale.wav",
            size_bytes=100,
        )
        # list_pending should clean up entries with missing audio files
        pending = queue.list_pending(user_id=mock_user_id)
        assert len(pending) == 0, "Stale entry should be removed"


class TestClearUserQueue:
    def test_clear_user_queue(self, queue, fake_audio_file):
        user1 = "clear-user-1"
        user2 = "clear-user-2"
        for i in range(3):
            queue.enqueue(user1, f"omi-{i}", fake_audio_file, str(i).zfill(64), "audio/wav", f"f{i}.wav", 100)
        queue.enqueue(user2, "omi-other", fake_audio_file, "x" * 64, "audio/wav", "other.wav", 100)

        removed = queue.clear_user_queue(user1)
        assert removed == 3
        assert queue.queue_size(user_id=user1) == 0
        assert queue.queue_size(user_id=user2) == 1
