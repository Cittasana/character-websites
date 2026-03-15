"""
Privacy controls for voice data — delete, reset, and sync management.

These controls call the backend API endpoints defined in Phase 13 requirements:
  DELETE /api/upload/voice/:recordingId    — delete individual recording
  DELETE /api/upload/voice/all            — delete all voice data + reset profile
  PATCH  /api/upload/voice/settings       — update sync settings (exclude periods, toggle)

All endpoints require JWT auth with the owner's token — enforced by backend.

Sync status:
  GET /api/omi/sync/status                — returns last_sync_at, recordings_count, etc.
"""
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import httpx

from omi.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExcludePeriod:
    """Time window to exclude from sync (recordings within this window won't be uploaded)."""
    from_dt: datetime       # start of exclusion window
    to_dt: datetime         # end of exclusion window

    def to_dict(self) -> dict:
        return {
            "from": self.from_dt.isoformat(),
            "to": self.to_dt.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExcludePeriod":
        return cls(
            from_dt=datetime.fromisoformat(data["from"]),
            to_dt=datetime.fromisoformat(data["to"]),
        )


@dataclass
class SyncSettings:
    """User's sync preferences."""
    sync_enabled: bool = True
    exclude_period: Optional[ExcludePeriod] = None

    def to_dict(self) -> dict:
        d: dict = {"sync_enabled": self.sync_enabled}
        if self.exclude_period:
            d["exclude_period"] = self.exclude_period.to_dict()
        else:
            d["exclude_period"] = None
        return d


@dataclass
class SyncStatus:
    """
    Sync state for the mobile app dashboard.
    Returned by GET /api/omi/sync/status.
    """
    last_sync_at: Optional[datetime]
    recordings_count: int
    pending_uploads: int            # items in offline queue
    sync_enabled: bool
    is_paired: bool

    def to_dict(self) -> dict:
        return {
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "recordings_count": self.recordings_count,
            "pending_uploads": self.pending_uploads,
            "sync_enabled": self.sync_enabled,
            "is_paired": self.is_paired,
        }


@dataclass
class DeletionResult:
    """Result of a delete operation."""
    deleted_recording_ids: list[str]
    deleted_count: int
    profile_reset: bool


class PrivacyControls:
    """
    Implements user privacy controls for voice data.

    All operations hit backend API endpoints — no direct DB access.
    Backend enforces ownership via JWT (only the owner can delete their data).
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
                timeout=60.0,   # deletions can take a moment (S3 + DB)
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # ── Individual recording deletion ─────────────────────────────────────

    async def delete_recording(self, recording_id: str) -> DeletionResult:
        """
        Delete a single voice recording.
        Removes: S3 file + DB row (backend handles both).

        Requires: JWT token of the recording owner.
        Returns DeletionResult.
        """
        logger.info(f"Requesting deletion of recording {recording_id}")

        try:
            response = await self.http_client.delete(
                f"/api/upload/voice/{recording_id}"
            )
            if response.status_code == 404:
                logger.warning(f"Recording {recording_id} not found")
                return DeletionResult(
                    deleted_recording_ids=[],
                    deleted_count=0,
                    profile_reset=False,
                )
            response.raise_for_status()

            logger.info(f"Recording {recording_id} deleted successfully")
            return DeletionResult(
                deleted_recording_ids=[recording_id],
                deleted_count=1,
                profile_reset=False,
            )

        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Delete recording {recording_id} failed: "
                f"{exc.response.status_code} {exc.response.text[:100]}"
            )
            raise PrivacyOperationError(
                f"Delete failed: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise PrivacyOperationError(f"Network error: {exc}") from exc

    # ── Full data wipe ────────────────────────────────────────────────────

    async def delete_all_voice_data(self, also_reset_personality: bool = True) -> DeletionResult:
        """
        Delete ALL voice recordings + optionally reset personality profile.

        This is the nuclear option — user wants a clean slate.
        The backend deletes:
        - All recordings in recordings table for this user
        - Associated S3 files
        - personality_schemas records (if also_reset_personality=True)
        - Personality analysis data from Claude

        Returns DeletionResult with count of deleted recordings.
        """
        logger.info(
            f"Requesting deletion of ALL voice data "
            f"(reset_personality={also_reset_personality})"
        )

        params = {}
        if also_reset_personality:
            params["reset_personality"] = "true"

        try:
            response = await self.http_client.delete(
                "/api/upload/voice/all",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            deleted_count = data.get("deleted_count", 0)
            recording_ids = data.get("deleted_recording_ids", [])
            profile_reset = data.get("profile_reset", also_reset_personality)

            logger.info(
                f"Deleted {deleted_count} recordings, "
                f"profile_reset={profile_reset}"
            )
            return DeletionResult(
                deleted_recording_ids=recording_ids,
                deleted_count=deleted_count,
                profile_reset=profile_reset,
            )

        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Delete all voice data failed: "
                f"{exc.response.status_code} {exc.response.text[:100]}"
            )
            raise PrivacyOperationError(
                f"Delete all failed: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise PrivacyOperationError(f"Network error: {exc}") from exc

    # ── Sync settings ─────────────────────────────────────────────────────

    async def update_sync_settings(self, settings: SyncSettings) -> SyncSettings:
        """
        Update the user's sync settings.

        - sync_enabled=False: pause automatic sync (recordings accumulate on Omi device)
        - exclude_period: don't sync recordings from this time window
        """
        payload = settings.to_dict()
        logger.info(
            f"Updating sync settings: enabled={settings.sync_enabled}, "
            f"exclude={settings.exclude_period}"
        )

        try:
            response = await self.http_client.patch(
                "/api/upload/voice/settings",
                json=payload,
            )
            response.raise_for_status()
            updated = response.json()

            # Parse response back to SyncSettings
            result = SyncSettings(sync_enabled=updated.get("sync_enabled", True))
            if updated.get("exclude_period"):
                result.exclude_period = ExcludePeriod.from_dict(updated["exclude_period"])

            logger.info("Sync settings updated successfully")
            return result

        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Update sync settings failed: {exc.response.status_code}"
            )
            raise PrivacyOperationError(
                f"Settings update failed: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise PrivacyOperationError(f"Network error: {exc}") from exc

    async def get_sync_settings(self) -> SyncSettings:
        """Fetch current sync settings."""
        try:
            response = await self.http_client.get("/api/upload/voice/settings")
            response.raise_for_status()
            data = response.json()
            result = SyncSettings(sync_enabled=data.get("sync_enabled", True))
            if data.get("exclude_period"):
                result.exclude_period = ExcludePeriod.from_dict(data["exclude_period"])
            return result
        except httpx.HTTPStatusError:
            return SyncSettings()  # default: enabled, no exclusions
        except httpx.RequestError:
            return SyncSettings()

    # ── Sync status ───────────────────────────────────────────────────────

    async def get_sync_status(self, pending_uploads: int = 0) -> SyncStatus:
        """
        Retrieve sync status for the mobile app dashboard.

        Calls the backend for stored state, supplements with local queue count.

        Args:
            pending_uploads: Count of items in the local offline queue
                             (the Omi layer tracks this; not stored in backend)
        """
        try:
            response = await self.http_client.get("/api/omi/sync/status")
            response.raise_for_status()
            data = response.json()

            last_sync_at = None
            if data.get("last_sync_at"):
                try:
                    last_sync_at = datetime.fromisoformat(
                        data["last_sync_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            return SyncStatus(
                last_sync_at=last_sync_at,
                recordings_count=data.get("recordings_count", 0),
                pending_uploads=pending_uploads,    # augment with local queue count
                sync_enabled=data.get("sync_enabled", True),
                is_paired=data.get("is_paired", False),
            )

        except httpx.HTTPStatusError as exc:
            logger.error(f"Get sync status failed: {exc.response.status_code}")
            # Return a safe default rather than raising
            return SyncStatus(
                last_sync_at=None,
                recordings_count=0,
                pending_uploads=pending_uploads,
                sync_enabled=True,
                is_paired=False,
            )
        except httpx.RequestError as exc:
            logger.error(f"Get sync status network error: {exc}")
            return SyncStatus(
                last_sync_at=None,
                recordings_count=0,
                pending_uploads=pending_uploads,
                sync_enabled=True,
                is_paired=False,
            )

    async def update_last_sync(self, synced_at: Optional[datetime] = None) -> bool:
        """
        Record the timestamp of the last successful sync in the backend.
        Called after each successful sync cycle.
        """
        now = synced_at or datetime.now(timezone.utc)
        try:
            response = await self.http_client.patch(
                "/api/omi/sync/status",
                json={"last_sync_at": now.isoformat()},
            )
            return response.status_code in (200, 204)
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.error(f"Failed to update last_sync_at: {exc}")
            return False


class PrivacyOperationError(Exception):
    """Raised when a privacy control operation fails."""
    pass
