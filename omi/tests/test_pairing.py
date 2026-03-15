"""
Tests for device pairing (Phase 11 - Plans 11-01, 11-02, 11-03, 11-04).

Tests cover:
- OAuth URL generation (state token format, CSRF)
- DevicePairingData construction
- PairingStatus serialization
- Token refresh detection
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from omi.pairing.oauth import OmiOAuthClient, OmiTokens, OmiAuthError
from omi.pairing.device_manager import DeviceManager, DevicePairingData, PairingStatus
from omi.pairing.bluetooth import BluetoothPairer, DiscoveredDevice, OMI_BLE_SERVICE_UUID


class TestOmiTokens:
    def test_token_not_expired_no_expiry(self):
        tokens = OmiTokens(
            access_token="abc", refresh_token=None,
            token_type="Bearer", expires_in=None, scope=""
        )
        assert not tokens.is_expired

    def test_token_not_expired_future(self):
        tokens = OmiTokens(
            access_token="abc", refresh_token=None,
            token_type="Bearer", expires_in=3600, scope=""
        )
        assert not tokens.is_expired

    def test_token_expired(self):
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        tokens = OmiTokens(
            access_token="abc", refresh_token=None,
            token_type="Bearer", expires_in=60, scope="",
            obtained_at=past
        )
        assert tokens.is_expired

    def test_to_dict_round_trip(self):
        tokens = OmiTokens(
            access_token="tok123",
            refresh_token="ref456",
            token_type="Bearer",
            expires_in=3600,
            scope="conversations:read",
            uid="firebase-uid-789",
        )
        d = tokens.to_dict()
        restored = OmiTokens.from_dict(d)
        assert restored.access_token == tokens.access_token
        assert restored.refresh_token == tokens.refresh_token
        assert restored.uid == tokens.uid


class TestOmiOAuthClient:
    def test_get_authorization_url_format(self, monkeypatch):
        monkeypatch.setenv("OMI_APP_ID", "test-app-id")
        monkeypatch.setenv("OMI_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("OMI_CLIENT_SECRET", "test-secret")
        from omi.config import get_settings
        get_settings.cache_clear()

        client = OmiOAuthClient()
        url, state = client.get_authorization_url()

        assert "test-app-id" in url
        assert "state=" in url
        assert len(state) > 20  # token is at least 20 chars

        get_settings.cache_clear()

    def test_get_authorization_url_unique_states(self, monkeypatch):
        monkeypatch.setenv("OMI_APP_ID", "app-id")
        from omi.config import get_settings
        get_settings.cache_clear()

        client = OmiOAuthClient()
        _, state1 = client.get_authorization_url()
        _, state2 = client.get_authorization_url()
        assert state1 != state2

        get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, monkeypatch):
        monkeypatch.setenv("OMI_CLIENT_ID", "cid")
        monkeypatch.setenv("OMI_CLIENT_SECRET", "csec")
        monkeypatch.setenv("OMI_OAUTH_REDIRECT_URI", "http://localhost/callback")
        from omi.config import get_settings
        get_settings.cache_clear()

        client = OmiOAuthClient()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "conversations:read",
            "uid": "firebase-uid",
        }

        with patch.object(client.http_client, "post", new_callable=AsyncMock, return_value=mock_response):
            tokens = await client.exchange_code("auth-code-123")

        assert tokens.access_token == "new-access-token"
        assert tokens.refresh_token == "new-refresh-token"
        assert tokens.uid == "firebase-uid"

        get_settings.cache_clear()


class TestPairingStatus:
    def test_pairing_status_to_dict_paired(self):
        now = datetime.now(timezone.utc)
        status = PairingStatus(
            is_paired=True,
            device_id="aabbccddeeff",
            last_seen=now,
            battery_level=85,
        )
        d = status.to_dict()
        assert d["is_paired"] is True
        assert d["device_id"] == "aabbccddeeff"
        assert d["battery_level"] == 85
        assert d["last_seen"] is not None

    def test_pairing_status_to_dict_unpaired(self):
        status = PairingStatus(
            is_paired=False,
            device_id=None,
            last_seen=None,
            battery_level=None,
        )
        d = status.to_dict()
        assert d["is_paired"] is False
        assert d["device_id"] is None
        assert d["last_seen"] is None
        assert d["battery_level"] is None


class TestDevicePairingData:
    def test_device_pairing_data_to_dict(self):
        data = DevicePairingData(
            user_id="user-uuid-123",
            device_id="aabbccddeeff",
            omi_uid="firebase-uid",
            omi_access_token="access-token",
            omi_refresh_token="refresh-token",
            token_expires_at="2026-12-31T00:00:00+00:00",
            paired_at=datetime.now(timezone.utc).isoformat(),
        )
        d = data.to_dict()
        assert d["user_id"] == "user-uuid-123"
        assert d["device_id"] == "aabbccddeeff"
        assert d["is_active"] is True


class TestBluetoothPairer:
    def test_parse_device_id_from_address(self):
        pairer = BluetoothPairer()
        device_id = pairer.parse_device_id_from_address("AA:BB:CC:DD:EE:FF")
        assert device_id == "aabbccddeeff"

    def test_is_omi_device_by_service_uuid(self):
        device = DiscoveredDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="Unknown",
            rssi=-70,
            service_uuids=[OMI_BLE_SERVICE_UUID],
        )
        assert device.is_omi_device

    def test_is_omi_device_by_name(self):
        device = DiscoveredDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="OMI-Device-001",
            rssi=-65,
            service_uuids=[],
        )
        assert device.is_omi_device

    def test_is_not_omi_device(self):
        device = DiscoveredDevice(
            address="11:22:33:44:55:66",
            name="AirPods Pro",
            rssi=-80,
            service_uuids=["random-uuid-1234"],
        )
        assert not device.is_omi_device
