"""
Tests for privacy controls (Phase 13 - Plans 13-03, 13-04).

Tests cover:
- SyncSettings serialization
- ExcludePeriod parsing
- SyncStatus to_dict
- PrivacyControls HTTP calls (mocked)
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from omi.privacy.controls import (
    PrivacyControls,
    SyncSettings,
    SyncStatus,
    ExcludePeriod,
    DeletionResult,
    PrivacyOperationError,
)


class TestExcludePeriod:
    def test_to_dict_format(self):
        now = datetime.now(timezone.utc)
        later = now + timedelta(hours=8)
        ep = ExcludePeriod(from_dt=now, to_dt=later)
        d = ep.to_dict()
        assert "from" in d
        assert "to" in d

    def test_from_dict_round_trip(self):
        now = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        later = datetime(2026, 3, 15, 18, 0, 0, tzinfo=timezone.utc)
        ep = ExcludePeriod(from_dt=now, to_dt=later)
        d = ep.to_dict()
        restored = ExcludePeriod.from_dict(d)
        assert restored.from_dt == ep.from_dt
        assert restored.to_dt == ep.to_dt


class TestSyncSettings:
    def test_to_dict_sync_enabled(self):
        settings = SyncSettings(sync_enabled=True)
        d = settings.to_dict()
        assert d["sync_enabled"] is True
        assert d["exclude_period"] is None

    def test_to_dict_with_exclude_period(self):
        now = datetime.now(timezone.utc)
        ep = ExcludePeriod(from_dt=now, to_dt=now + timedelta(hours=2))
        settings = SyncSettings(sync_enabled=True, exclude_period=ep)
        d = settings.to_dict()
        assert d["exclude_period"] is not None
        assert "from" in d["exclude_period"]

    def test_to_dict_sync_disabled(self):
        settings = SyncSettings(sync_enabled=False)
        d = settings.to_dict()
        assert d["sync_enabled"] is False


class TestSyncStatus:
    def test_to_dict_fully_synced(self):
        now = datetime.now(timezone.utc)
        status = SyncStatus(
            last_sync_at=now,
            recordings_count=15,
            pending_uploads=0,
            sync_enabled=True,
            is_paired=True,
        )
        d = status.to_dict()
        assert d["recordings_count"] == 15
        assert d["pending_uploads"] == 0
        assert d["sync_enabled"] is True
        assert d["is_paired"] is True
        assert d["last_sync_at"] is not None

    def test_to_dict_never_synced(self):
        status = SyncStatus(
            last_sync_at=None,
            recordings_count=0,
            pending_uploads=3,
            sync_enabled=True,
            is_paired=False,
        )
        d = status.to_dict()
        assert d["last_sync_at"] is None
        assert d["pending_uploads"] == 3


class TestDeletionResult:
    def test_single_deletion(self):
        result = DeletionResult(
            deleted_recording_ids=["rec-uuid-1"],
            deleted_count=1,
            profile_reset=False,
        )
        assert result.deleted_count == 1
        assert not result.profile_reset

    def test_bulk_deletion(self):
        ids = [f"rec-{i}" for i in range(5)]
        result = DeletionResult(
            deleted_recording_ids=ids,
            deleted_count=5,
            profile_reset=True,
        )
        assert result.deleted_count == 5
        assert result.profile_reset


class TestPrivacyControlsAPI:
    """Tests for PrivacyControls HTTP calls (all backend calls are mocked)."""

    @pytest.mark.asyncio
    async def test_delete_recording_success(self, mock_user_jwt):
        controls = PrivacyControls(user_jwt=mock_user_jwt)
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            controls.http_client, "delete", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await controls.delete_recording("rec-uuid-123")

        assert result.deleted_count == 1
        assert result.deleted_recording_ids == ["rec-uuid-123"]

    @pytest.mark.asyncio
    async def test_delete_recording_not_found(self, mock_user_jwt):
        controls = PrivacyControls(user_jwt=mock_user_jwt)
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(
            controls.http_client, "delete", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await controls.delete_recording("nonexistent-id")

        assert result.deleted_count == 0

    @pytest.mark.asyncio
    async def test_delete_all_success(self, mock_user_jwt):
        controls = PrivacyControls(user_jwt=mock_user_jwt)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "deleted_count": 12,
            "deleted_recording_ids": [f"rec-{i}" for i in range(12)],
            "profile_reset": True,
        }

        with patch.object(
            controls.http_client, "delete", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await controls.delete_all_voice_data()

        assert result.deleted_count == 12
        assert result.profile_reset is True

    @pytest.mark.asyncio
    async def test_update_sync_settings_disables_sync(self, mock_user_jwt):
        controls = PrivacyControls(user_jwt=mock_user_jwt)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "sync_enabled": False,
            "exclude_period": None,
        }

        with patch.object(
            controls.http_client, "patch", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await controls.update_sync_settings(SyncSettings(sync_enabled=False))

        assert result.sync_enabled is False

    @pytest.mark.asyncio
    async def test_get_sync_status_returns_defaults_on_error(self, mock_user_jwt):
        controls = PrivacyControls(user_jwt=mock_user_jwt)
        import httpx
        with patch.object(
            controls.http_client, "get",
            new_callable=AsyncMock,
            side_effect=httpx.RequestError("connection refused")
        ):
            status = await controls.get_sync_status(pending_uploads=5)

        # Should return safe defaults, not raise
        assert status.pending_uploads == 5
        assert status.recordings_count == 0
        assert status.last_sync_at is None
