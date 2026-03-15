"""
Sync Orchestrator — the main coordination loop for the Omi audio sync pipeline.

This is the top-level entry point that:
1. Checks device pairing status
2. Ensures OAuth tokens are fresh
3. Polls Omi API for new recordings
4. Downloads each to an encrypted temp buffer
5. Runs Whisper transcription fallback if needed
6. Detects language
7. Extracts acoustic features via librosa
8. Checks for duplicates
9. Uploads to /api/upload/voice
10. Processes the offline queue (retry failed uploads)
11. Updates sync status

Run this on a schedule (e.g. every 5 minutes via cron, Celery beat, or APScheduler).

Usage:
    orchestrator = SyncOrchestrator(user_id="uuid", user_jwt="jwt-token")
    result = await orchestrator.run_sync_cycle()
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from omi.config import get_settings
from omi.pairing.device_manager import DeviceManager, DevicePairingError
from omi.sync.detector import RecordingDetector, OmiRecording, OmiTokenExpiredError, OmiAPIError
from omi.sync.downloader import AudioDownloader, AudioDownloadError
from omi.sync.uploader import AudioUploader, UploadResult, UploadNetworkError, DuplicateRecordingError, UploadError
from omi.sync.deduplicator import RecordingDeduplicator
from omi.sync.queue import OfflineQueue, QueueFullError, QueuedRecording
from omi.transcription.whisper_fallback import WhisperTranscriber
from omi.acoustic.extractor import AcousticExtractor, AcousticExtractionError
from omi.privacy.controls import PrivacyControls, SyncSettings

logger = logging.getLogger(__name__)


@dataclass
class SyncCycleResult:
    """Summary of one sync cycle."""
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Counters
    new_recordings_detected: int = 0
    recordings_uploaded: int = 0
    recordings_skipped_duplicate: int = 0
    recordings_queued_offline: int = 0
    queue_retries_succeeded: int = 0
    queue_retries_failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "new_recordings_detected": self.new_recordings_detected,
            "recordings_uploaded": self.recordings_uploaded,
            "recordings_skipped_duplicate": self.recordings_skipped_duplicate,
            "recordings_queued_offline": self.recordings_queued_offline,
            "queue_retries_succeeded": self.queue_retries_succeeded,
            "queue_retries_failed": self.queue_retries_failed,
            "errors": self.errors,
            "success": self.success,
        }


class SyncOrchestrator:
    """
    Orchestrates the full Omi → backend audio sync pipeline for one user.

    Each instance is scoped to a single user (user_id + user_jwt).
    For multi-user setups, instantiate one orchestrator per user.
    """

    def __init__(
        self,
        user_id: str,
        user_jwt: str,
        last_sync_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.user_jwt = user_jwt
        self.last_sync_at = last_sync_at
        self.settings = get_settings()

        # Initialize all subsystems
        self._device_manager = DeviceManager(backend_jwt=user_jwt)
        self._downloader = AudioDownloader()
        self._transcriber = WhisperTranscriber()
        self._extractor = AcousticExtractor()
        self._queue = OfflineQueue()
        self._deduplicator = RecordingDeduplicator(user_jwt=user_jwt)
        self._uploader = AudioUploader(user_jwt=user_jwt, downloader=self._downloader)
        self._privacy = PrivacyControls(user_jwt=user_jwt)

    async def run_sync_cycle(self) -> SyncCycleResult:
        """
        Run a complete sync cycle for this user.

        Returns SyncCycleResult with full details of what happened.
        """
        now = datetime.now(timezone.utc)
        result = SyncCycleResult(user_id=self.user_id, started_at=now)

        logger.info(
            f"Starting sync cycle for user {self.user_id[:8]} "
            f"(last_sync={self.last_sync_at.isoformat() if self.last_sync_at else 'never'})"
        )

        try:
            # 1. Check sync settings (user may have disabled sync)
            sync_settings = await self._privacy.get_sync_settings()
            if not sync_settings.sync_enabled:
                logger.info(f"Sync disabled for user {self.user_id[:8]} — skipping")
                result.completed_at = datetime.now(timezone.utc)
                return result

            # 2. Get fresh Omi access token
            access_token = await self._device_manager.ensure_token_fresh(
                self.user_id, user_jwt=self.user_jwt
            )
            if not access_token:
                msg = f"No valid Omi access token for user {self.user_id[:8]}"
                logger.warning(msg)
                result.errors.append(msg)
                result.completed_at = datetime.now(timezone.utc)
                return result

            # 3. Detect new recordings
            detector = RecordingDetector(access_token=access_token)
            try:
                new_recordings = await detector.fetch_new_recordings(
                    since=self.last_sync_at
                )
            except OmiTokenExpiredError:
                msg = "Omi access token expired during sync"
                logger.error(msg)
                result.errors.append(msg)
                result.completed_at = datetime.now(timezone.utc)
                return result
            except OmiAPIError as exc:
                msg = f"Omi API error: {exc}"
                logger.error(msg)
                result.errors.append(msg)
                result.completed_at = datetime.now(timezone.utc)
                return result
            finally:
                await detector.close()

            result.new_recordings_detected = len(new_recordings)
            logger.info(f"Found {len(new_recordings)} new recording(s)")

            # Filter out excluded periods
            new_recordings = self._filter_excluded_period(new_recordings, sync_settings)

            # 4. Process each new recording
            for recording in new_recordings:
                await self._process_recording(recording, access_token, result)

            # 5. Process offline queue (retry failed uploads)
            await self._process_offline_queue(result)

            # 6. Update last_sync_at
            if result.recordings_uploaded > 0 or result.new_recordings_detected > 0:
                await self._privacy.update_last_sync(now)
                self.last_sync_at = now

            # 7. Update device last_seen
            await self._device_manager.update_last_seen(
                self.user_id, user_jwt=self.user_jwt
            )

        except Exception as exc:
            msg = f"Unexpected error in sync cycle: {exc}"
            logger.exception(msg)
            result.errors.append(msg)
        finally:
            result.completed_at = datetime.now(timezone.utc)
            logger.info(
                f"Sync cycle complete: {result.recordings_uploaded} uploaded, "
                f"{result.recordings_queued_offline} queued, "
                f"{result.queue_retries_succeeded} retried, "
                f"duration={result.duration_seconds:.1f}s"
            )

        return result

    async def _process_recording(
        self,
        recording: OmiRecording,
        access_token: str,
        result: SyncCycleResult,
    ) -> None:
        """Process a single new recording: download, deduplicate, transcribe, analyze, upload."""
        try:
            # Download with encryption
            async with self._downloader.download(recording, access_token=access_token) as downloaded:
                # Deduplication check
                is_dup = await self._deduplicator.is_duplicate(
                    sha256_hash=downloaded.sha256_hash,
                    omi_conversation_id=recording.id,
                )
                if is_dup:
                    logger.info(f"Skipping duplicate: {recording.id}")
                    result.recordings_skipped_duplicate += 1
                    return

                # Transcription: use Omi's transcript if available, else Whisper
                transcript = recording.transcript_text
                transcript_source = "omi" if transcript else None

                if not transcript:
                    logger.info(
                        f"No Omi transcript for {recording.id} — running Whisper fallback"
                    )
                    audio_bytes = self._downloader.decrypt(downloaded.encrypted_path)
                    whisper_result = await self._transcriber.transcribe(
                        audio_bytes,
                        content_type=downloaded.content_type,
                    )
                    if whisper_result and not whisper_result.is_empty:
                        transcript = whisper_result.text
                        transcript_source = whisper_result.source
                        recording.language = recording.language or whisper_result.language

                # Language detection (if still missing)
                language = recording.language
                if not language and transcript:
                    language = self._transcriber.detect_language(transcript)

                # Acoustic extraction
                acoustic_metadata = None
                try:
                    audio_bytes_for_analysis = self._downloader.decrypt(
                        downloaded.encrypted_path
                    )
                    features = self._extractor.extract(
                        audio_input=audio_bytes_for_analysis,
                        content_type=downloaded.content_type,
                        transcript=transcript,
                    )
                    acoustic_metadata = features.to_dict()
                    logger.debug(
                        f"Acoustic features extracted for {recording.id}: "
                        f"pitch_mean={features.pitch_range.mean_hz:.1f}Hz, "
                        f"tempo={features.speech_rhythm.tempo_bpm:.1f}BPM"
                    )
                except AcousticExtractionError as exc:
                    logger.warning(f"Acoustic extraction failed for {recording.id}: {exc}")
                    # Non-fatal: upload without acoustic data

                # Upload (acoustic_metadata is attached to the backend recording,
                # which the Celery job reads from the DB when triggering Claude analysis)
                try:
                    upload_result = await self._uploader.upload_from_buffer(
                        downloaded,
                        transcript=transcript,
                        transcript_source=transcript_source,
                        language=language,
                        duration_seconds=recording.duration_seconds,
                    )
                    result.recordings_uploaded += 1
                    logger.info(
                        f"Uploaded recording {recording.id} -> backend id={upload_result.recording_id}"
                    )

                    # If acoustic features were extracted, attach them to the recording
                    if acoustic_metadata:
                        await self._attach_acoustic_metadata(
                            upload_result.recording_id, acoustic_metadata
                        )

                except DuplicateRecordingError:
                    result.recordings_skipped_duplicate += 1

                except UploadNetworkError as exc:
                    # Queue for retry
                    logger.warning(
                        f"Network error uploading {recording.id}, queuing for retry: {exc}"
                    )
                    self._queue_recording(recording, downloaded, transcript, transcript_source, language, result)

                except UploadError as exc:
                    logger.error(f"Upload failed for {recording.id}: {exc}")
                    result.errors.append(f"Upload failed for {recording.id}: {exc}")

        except AudioDownloadError as exc:
            logger.error(f"Download failed for {recording.id}: {exc}")
            result.errors.append(f"Download failed for {recording.id}: {exc}")

        except Exception as exc:
            logger.exception(f"Unexpected error processing {recording.id}: {exc}")
            result.errors.append(f"Error processing {recording.id}: {exc}")

    def _queue_recording(
        self,
        recording: OmiRecording,
        downloaded,
        transcript: Optional[str],
        transcript_source: Optional[str],
        language: Optional[str],
        result: SyncCycleResult,
    ) -> None:
        """Add a failed recording to the offline queue."""
        try:
            self._queue.enqueue(
                user_id=self.user_id,
                omi_recording_id=recording.id,
                encrypted_audio_path=str(downloaded.encrypted_path),
                sha256_hash=downloaded.sha256_hash,
                content_type=downloaded.content_type,
                filename=downloaded.filename,
                size_bytes=downloaded.size_bytes,
                transcript=transcript,
                transcript_source=transcript_source,
                language=language,
                duration_seconds=recording.duration_seconds,
            )
            result.recordings_queued_offline += 1
        except QueueFullError as exc:
            logger.error(f"Offline queue full: {exc}")
            result.errors.append(str(exc))

    async def _process_offline_queue(self, result: SyncCycleResult) -> None:
        """Process ready-to-retry entries from the offline queue."""
        ready = self._queue.list_ready_to_retry(user_id=self.user_id)
        if not ready:
            return

        logger.info(f"Processing {len(ready)} queued recordings for user {self.user_id[:8]}")

        for entry in ready:
            try:
                from pathlib import Path
                audio_path = Path(entry.encrypted_audio_path)
                if not audio_path.exists():
                    logger.warning(
                        f"Encrypted audio gone for queue entry {entry.queue_id}, removing"
                    )
                    self._queue.mark_failed(entry.queue_id, "audio file missing")
                    continue

                # Decrypt and upload
                audio_bytes = self._downloader.decrypt(audio_path)

                # Re-check dedup
                is_dup = await self._deduplicator.is_duplicate(
                    sha256_hash=entry.sha256_hash,
                    omi_conversation_id=entry.omi_recording_id,
                )
                if is_dup:
                    self._queue.mark_succeeded(entry.queue_id)
                    result.queue_retries_succeeded += 1
                    continue

                import io, tempfile, os
                from pathlib import Path as Pth

                # Write plaintext audio to a temp file for uploader
                import hashlib
                from omi.sync.downloader import _mime_to_ext
                ext = _mime_to_ext(entry.content_type)

                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                try:
                    upload_result = await self._uploader.upload_from_path(
                        audio_path=Pth(tmp_path),
                        recording_id=entry.omi_recording_id,
                        content_type=entry.content_type,
                        transcript=entry.transcript,
                        transcript_source=entry.transcript_source,
                        language=entry.language,
                        duration_seconds=entry.duration_seconds,
                    )
                    self._queue.mark_succeeded(entry.queue_id)
                    result.queue_retries_succeeded += 1
                    logger.info(
                        f"Queue retry succeeded: {entry.queue_id} -> "
                        f"recording_id={upload_result.recording_id}"
                    )
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

            except DuplicateRecordingError:
                self._queue.mark_succeeded(entry.queue_id)
                result.queue_retries_succeeded += 1

            except UploadNetworkError as exc:
                self._queue.mark_failed(entry.queue_id, str(exc))
                result.queue_retries_failed += 1

            except Exception as exc:
                logger.error(f"Queue retry error for {entry.queue_id}: {exc}")
                self._queue.mark_failed(entry.queue_id, str(exc))
                result.queue_retries_failed += 1

    async def _attach_acoustic_metadata(
        self, recording_id: str, acoustic_metadata: dict
    ) -> None:
        """
        Attach acoustic features to the backend recording after upload.
        The backend PATCH endpoint stores them in recordings.acoustic_metadata,
        which the Celery worker reads when dispatching the Claude analysis job.
        """
        import httpx
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.BACKEND_API_URL,
                headers={"Authorization": f"Bearer {self.user_jwt}"},
                timeout=15.0,
            ) as client:
                response = await client.patch(
                    f"/api/upload/voice/{recording_id}/acoustic",
                    json={"acoustic_metadata": acoustic_metadata},
                )
                if response.status_code in (200, 204):
                    logger.debug(f"Acoustic metadata attached to recording {recording_id}")
                else:
                    logger.warning(
                        f"Failed to attach acoustic metadata to {recording_id}: "
                        f"{response.status_code}"
                    )
        except httpx.RequestError as exc:
            logger.warning(f"Could not attach acoustic metadata: {exc}")

    def _filter_excluded_period(
        self,
        recordings: list[OmiRecording],
        sync_settings: SyncSettings,
    ) -> list[OmiRecording]:
        """Filter out recordings that fall within a user-specified exclusion period."""
        if not sync_settings.exclude_period:
            return recordings

        ep = sync_settings.exclude_period
        filtered = []
        for r in recordings:
            if ep.from_dt <= r.created_at <= ep.to_dt:
                logger.debug(
                    f"Skipping recording {r.id} in excluded period "
                    f"({ep.from_dt.date()} - {ep.to_dt.date()})"
                )
            else:
                filtered.append(r)

        excluded_count = len(recordings) - len(filtered)
        if excluded_count:
            logger.info(f"Excluded {excluded_count} recording(s) per user privacy settings")

        return filtered

    async def close(self):
        """Clean up HTTP clients."""
        await self._device_manager.close()
        await self._downloader.close()
        await self._uploader.close()
        await self._deduplicator.close()
        await self._privacy.close()


async def run_sync_for_user(
    user_id: str,
    user_jwt: str,
    last_sync_at: Optional[datetime] = None,
) -> SyncCycleResult:
    """
    Convenience function: run one sync cycle for a user.
    Used by Celery beat tasks or background schedulers.
    """
    orchestrator = SyncOrchestrator(
        user_id=user_id,
        user_jwt=user_jwt,
        last_sync_at=last_sync_at,
    )
    try:
        return await orchestrator.run_sync_cycle()
    finally:
        await orchestrator.close()
