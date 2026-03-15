"""
Offline queue — stores failed uploads locally and retries with exponential backoff.

When the backend is unreachable or the user has no internet:
1. Serialize the recording metadata + encrypted audio path to a JSON queue file
2. On next connectivity check, process queued items
3. Exponential backoff: 2s, 4s, 8s, 16s, 32s (then give up until next poll cycle)

Queue storage: JSON file per queued recording in OFFLINE_QUEUE_PATH directory.
Each file is named by a UUID and contains the serialized QueuedRecording.

Note: The encrypted audio file must still exist on disk for re-upload.
If the encrypted file was deleted (e.g. after system restart), the queue entry
is marked as stale and removed.
"""
import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from omi.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class QueuedRecording:
    """A recording queued for retry upload."""
    queue_id: str                           # Local queue entry UUID
    user_id: str                            # Character-Websites user UUID
    omi_recording_id: str                   # Omi conversation ID
    encrypted_audio_path: str              # Path to encrypted temp audio file
    sha256_hash: str                        # SHA-256 of plaintext audio
    content_type: str
    filename: str
    size_bytes: int
    transcript: Optional[str]              # Transcript (if available)
    transcript_source: Optional[str]       # 'omi' | 'whisper' | None
    language: Optional[str]
    duration_seconds: Optional[float]
    created_at: str                         # ISO datetime
    retry_count: int = 0
    last_retry_at: Optional[str] = None
    next_retry_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "QueuedRecording":
        return cls(**data)


class OfflineQueue:
    """
    Persistent offline queue for recordings that couldn't be uploaded.

    The queue directory contains one JSON file per queued recording.
    Queue entries are self-contained: they include all metadata needed
    for upload, plus a reference to the encrypted audio file path.
    """

    def __init__(self):
        self.settings = get_settings()
        self._queue_dir = Path(self.settings.OFFLINE_QUEUE_PATH)
        self._queue_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    def enqueue(
        self,
        user_id: str,
        omi_recording_id: str,
        encrypted_audio_path: str,
        sha256_hash: str,
        content_type: str,
        filename: str,
        size_bytes: int,
        transcript: Optional[str] = None,
        transcript_source: Optional[str] = None,
        language: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> QueuedRecording:
        """
        Add a recording to the offline queue.

        Returns the QueuedRecording that was enqueued.
        Raises QueueFullError if the queue is at max capacity.
        """
        current_count = len(self.list_pending())
        if current_count >= self.settings.OFFLINE_QUEUE_MAX_SIZE:
            raise QueueFullError(
                f"Offline queue is full ({current_count}/{self.settings.OFFLINE_QUEUE_MAX_SIZE})"
            )

        now = datetime.now(timezone.utc)
        queued = QueuedRecording(
            queue_id=str(uuid.uuid4()),
            user_id=user_id,
            omi_recording_id=omi_recording_id,
            encrypted_audio_path=encrypted_audio_path,
            sha256_hash=sha256_hash,
            content_type=content_type,
            filename=filename,
            size_bytes=size_bytes,
            transcript=transcript,
            transcript_source=transcript_source,
            language=language,
            duration_seconds=duration_seconds,
            created_at=now.isoformat(),
            error_message=error_message,
            next_retry_at=now.isoformat(),  # Eligible for retry immediately
        )

        self._write_entry(queued)
        logger.info(
            f"Enqueued recording {omi_recording_id} for user {user_id[:8]} "
            f"(queue_id={queued.queue_id})"
        )
        return queued

    def list_pending(self, user_id: Optional[str] = None) -> list[QueuedRecording]:
        """
        List all pending queue entries, optionally filtered by user_id.
        Returns only entries whose next_retry_at has passed (ready to retry).
        """
        entries = []
        now = datetime.now(timezone.utc)

        for path in self._queue_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                entry = QueuedRecording.from_dict(data)

                if user_id and entry.user_id != user_id:
                    continue

                # Check if encrypted audio file still exists
                if not Path(entry.encrypted_audio_path).exists():
                    logger.warning(
                        f"Queue entry {entry.queue_id}: encrypted audio file missing, "
                        f"removing stale entry"
                    )
                    path.unlink(missing_ok=True)
                    continue

                entries.append(entry)
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.warning(f"Corrupt queue entry {path}: {exc} — removing")
                path.unlink(missing_ok=True)

        return entries

    def list_ready_to_retry(self, user_id: Optional[str] = None) -> list[QueuedRecording]:
        """Return queue entries that are due for retry (next_retry_at <= now)."""
        now = datetime.now(timezone.utc)
        ready = []
        for entry in self.list_pending(user_id=user_id):
            if entry.next_retry_at is None:
                ready.append(entry)
                continue
            try:
                next_retry = datetime.fromisoformat(entry.next_retry_at)
                if now >= next_retry:
                    ready.append(entry)
            except ValueError:
                ready.append(entry)
        return ready

    def mark_succeeded(self, queue_id: str) -> bool:
        """Remove a queue entry after successful upload."""
        entry_path = self._queue_dir / f"{queue_id}.json"
        if entry_path.exists():
            entry_path.unlink()
            logger.info(f"Queue entry {queue_id} completed and removed")
            return True
        return False

    def mark_failed(
        self,
        queue_id: str,
        error_message: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Optional[QueuedRecording]:
        """
        Record a failed upload attempt. Compute next retry time via exponential backoff.
        Returns the updated entry, or None if max retries exceeded (entry removed).
        """
        max_retries = max_retries or self.settings.SYNC_RETRY_MAX_ATTEMPTS
        entry = self._read_entry(queue_id)
        if entry is None:
            return None

        entry.retry_count += 1
        entry.last_retry_at = datetime.now(timezone.utc).isoformat()
        entry.error_message = error_message

        if entry.retry_count >= max_retries:
            logger.warning(
                f"Queue entry {queue_id} exceeded max retries ({max_retries}), removing"
            )
            self._delete_entry(queue_id)
            return None

        # Exponential backoff: base_delay * 2^retry_count (capped at 1 hour)
        base = self.settings.SYNC_RETRY_BASE_DELAY_SECONDS
        delay_seconds = min(base * (2 ** entry.retry_count), 3600)
        next_retry_epoch = time.time() + delay_seconds
        entry.next_retry_at = datetime.fromtimestamp(
            next_retry_epoch, tz=timezone.utc
        ).isoformat()

        self._write_entry(entry)
        logger.info(
            f"Queue entry {queue_id} failed (attempt {entry.retry_count}/{max_retries}), "
            f"retry in {delay_seconds:.0f}s"
        )
        return entry

    def queue_size(self, user_id: Optional[str] = None) -> int:
        """Count pending queue entries."""
        return len(self.list_pending(user_id=user_id))

    def clear_user_queue(self, user_id: str) -> int:
        """Remove all queue entries for a user. Returns count removed."""
        removed = 0
        for entry in self.list_pending(user_id=user_id):
            self._delete_entry(entry.queue_id)
            removed += 1
        return removed

    # ── Private helpers ───────────────────────────────────────────────────

    def _entry_path(self, queue_id: str) -> Path:
        return self._queue_dir / f"{queue_id}.json"

    def _write_entry(self, entry: QueuedRecording):
        path = self._entry_path(entry.queue_id)
        path.write_text(json.dumps(entry.to_dict(), indent=2))
        path.chmod(0o600)

    def _read_entry(self, queue_id: str) -> Optional[QueuedRecording]:
        path = self._entry_path(queue_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return QueuedRecording.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning(f"Corrupt queue entry {queue_id}: {exc}")
            return None

    def _delete_entry(self, queue_id: str):
        path = self._entry_path(queue_id)
        path.unlink(missing_ok=True)


class QueueFullError(Exception):
    """Raised when the offline queue is at max capacity."""
    pass
