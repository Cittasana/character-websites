"""
Device Manager — links Omi device_id + omi_access_token to user_id in the backend.

Responsibilities:
- Store pairing data via backend API calls (we do NOT write to the DB directly)
- Retrieve pairing status for a given user_id
- Handle re-pairing (revoke old tokens, link new device)
- Handle device reset (clear tokens, keep user account)
- Return pairing status dict for the mobile app dashboard

The backend is expected to have an `/api/omi/devices` endpoint family.
If those don't exist yet, this module prepares the data structures and calls
so the Backend team can implement the matching routes in Phase 1-2.
"""
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import httpx

from omi.config import get_settings
from omi.pairing.oauth import OmiOAuthClient, OmiTokens, OmiAuthError

logger = logging.getLogger(__name__)


@dataclass
class DevicePairingData:
    """All data stored for a paired Omi device."""
    user_id: str                        # Character-Websites user UUID
    device_id: str                      # Omi device identifier (BLE address or omi uid)
    omi_uid: Optional[str]              # Omi cloud user UID (Firebase UID)
    omi_access_token: str               # OAuth access token
    omi_refresh_token: Optional[str]    # OAuth refresh token
    token_expires_at: Optional[str]     # ISO datetime string
    paired_at: str                      # ISO datetime string
    last_seen: Optional[str] = None     # ISO datetime string
    battery_level: Optional[int] = None
    is_active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PairingStatus:
    """
    Pairing status returned to the mobile app dashboard.
    Matches the shape specified in Phase 11 requirements.
    """
    is_paired: bool
    device_id: Optional[str]
    last_seen: Optional[datetime]
    battery_level: Optional[int]
    sync_enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "is_paired": self.is_paired,
            "device_id": self.device_id,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "battery_level": self.battery_level,
            "sync_enabled": self.sync_enabled,
        }


class DeviceManager:
    """
    Manages the link between Omi devices and Character-Websites user accounts.

    All persistence goes through the backend API (not direct DB access).
    The backend `/api/omi/devices` endpoints are the authority for device state.
    """

    def __init__(self, backend_jwt: Optional[str] = None):
        """
        Args:
            backend_jwt: JWT token for authenticating calls to the backend API.
                         In production, use a service-level token or the user's JWT.
        """
        self.settings = get_settings()
        self.backend_jwt = backend_jwt or self.settings.BACKEND_JWT_SECRET
        self.oauth_client = OmiOAuthClient()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.backend_jwt:
                headers["Authorization"] = f"Bearer {self.backend_jwt}"
            self._http_client = httpx.AsyncClient(
                base_url=self.settings.BACKEND_API_URL,
                headers=headers,
                timeout=30.0,
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        await self.oauth_client.close()

    # ── Pairing ───────────────────────────────────────────────────────────

    async def pair_device(
        self,
        user_id: str,
        tokens: OmiTokens,
        device_id: Optional[str] = None,
        user_jwt: Optional[str] = None,
    ) -> DevicePairingData:
        """
        Complete the device pairing: store device_id + tokens linked to user_id.

        Args:
            user_id: The Character-Websites user UUID
            tokens: OAuth tokens obtained from Omi
            device_id: BLE device address (optional; derived from omi_uid if absent)
            user_jwt: The user's JWT for authenticating the backend API call
        """
        # Derive device_id from omi_uid if not provided via BLE
        effective_device_id = device_id or tokens.uid or f"omi-{user_id[:8]}"

        now = datetime.now(timezone.utc)
        pairing_data = DevicePairingData(
            user_id=user_id,
            device_id=effective_device_id,
            omi_uid=tokens.uid,
            omi_access_token=tokens.access_token,
            omi_refresh_token=tokens.refresh_token,
            token_expires_at=tokens.expires_at.isoformat() if tokens.expires_at else None,
            paired_at=now.isoformat(),
        )

        # Persist via backend API
        auth_header = f"Bearer {user_jwt}" if user_jwt else f"Bearer {self.backend_jwt}"
        try:
            response = await self.http_client.post(
                "/api/omi/devices",
                json=pairing_data.to_dict(),
                headers={"Authorization": auth_header},
            )
            response.raise_for_status()
            logger.info(
                f"Device paired: user_id={user_id} device_id={effective_device_id}"
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Failed to store pairing data: {exc.response.status_code} {exc.response.text}"
            )
            raise DevicePairingError(
                f"Backend rejected pairing data: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Backend unreachable during pairing: {exc}")
            raise DevicePairingError(f"Backend unavailable: {exc}") from exc

        return pairing_data

    # ── Re-pairing ────────────────────────────────────────────────────────

    async def repaire_device(
        self,
        user_id: str,
        new_tokens: OmiTokens,
        new_device_id: Optional[str] = None,
        user_jwt: Optional[str] = None,
    ) -> DevicePairingData:
        """
        Handle device replacement or reset:
        1. Fetch existing pairing data
        2. Revoke the old access token
        3. Store new device_id + tokens

        Raises DevicePairingError if the user has no existing pairing.
        """
        # Fetch existing pairing to revoke old token
        existing = await self.get_pairing_data(user_id, user_jwt=user_jwt)
        if existing:
            logger.info(
                f"Re-pairing: revoking old device {existing.device_id} for user {user_id}"
            )
            try:
                await self.oauth_client.revoke_token(existing.omi_access_token)
            except OmiAuthError as exc:
                # Non-fatal: log and continue — we're replacing the device anyway
                logger.warning(f"Could not revoke old token during re-pairing: {exc}")

            # Mark old device as inactive in backend
            await self._deactivate_device(user_id, existing.device_id, user_jwt=user_jwt)

        # Pair the new device
        return await self.pair_device(
            user_id=user_id,
            tokens=new_tokens,
            device_id=new_device_id,
            user_jwt=user_jwt,
        )

    async def unpair_device(self, user_id: str, user_jwt: Optional[str] = None) -> bool:
        """
        Fully unpair a device: revoke tokens, remove pairing record.
        Used when user explicitly disconnects their Omi device.
        """
        existing = await self.get_pairing_data(user_id, user_jwt=user_jwt)
        if not existing:
            logger.info(f"No device to unpair for user {user_id}")
            return False

        # Revoke OAuth token
        try:
            await self.oauth_client.revoke_token(existing.omi_access_token)
        except OmiAuthError as exc:
            logger.warning(f"Token revocation failed during unpair: {exc}")

        # Delete from backend
        auth_header = f"Bearer {user_jwt}" if user_jwt else f"Bearer {self.backend_jwt}"
        try:
            response = await self.http_client.delete(
                f"/api/omi/devices/{user_id}",
                headers={"Authorization": auth_header},
            )
            if response.status_code in (200, 204):
                logger.info(f"Successfully unpaired device for user {user_id}")
                return True
            logger.error(f"Failed to delete pairing record: {response.status_code}")
            return False
        except httpx.RequestError as exc:
            logger.error(f"Backend unreachable during unpair: {exc}")
            return False

    # ── Status ────────────────────────────────────────────────────────────

    async def get_pairing_status(
        self,
        user_id: str,
        user_jwt: Optional[str] = None,
    ) -> PairingStatus:
        """
        Return the pairing status dict for the mobile app dashboard.
        Shape: {is_paired, device_id, last_seen, battery_level, sync_enabled}
        """
        data = await self.get_pairing_data(user_id, user_jwt=user_jwt)
        if not data or not data.is_active:
            return PairingStatus(
                is_paired=False,
                device_id=None,
                last_seen=None,
                battery_level=None,
            )

        last_seen = None
        if data.last_seen:
            try:
                last_seen = datetime.fromisoformat(data.last_seen)
            except ValueError:
                pass

        return PairingStatus(
            is_paired=True,
            device_id=data.device_id,
            last_seen=last_seen,
            battery_level=data.battery_level,
        )

    async def get_pairing_data(
        self,
        user_id: str,
        user_jwt: Optional[str] = None,
    ) -> Optional[DevicePairingData]:
        """Fetch full pairing data for a user from the backend."""
        auth_header = f"Bearer {user_jwt}" if user_jwt else f"Bearer {self.backend_jwt}"
        try:
            response = await self.http_client.get(
                f"/api/omi/devices/{user_id}",
                headers={"Authorization": auth_header},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            raw = response.json()
            return DevicePairingData(**raw)
        except httpx.HTTPStatusError as exc:
            logger.error(f"Failed to fetch pairing data: {exc.response.status_code}")
            return None
        except httpx.RequestError as exc:
            logger.error(f"Backend unreachable: {exc}")
            return None

    async def update_last_seen(
        self,
        user_id: str,
        battery_level: Optional[int] = None,
        user_jwt: Optional[str] = None,
    ) -> bool:
        """Update last_seen timestamp and optional battery level for the device."""
        now = datetime.now(timezone.utc).isoformat()
        payload = {"last_seen": now}
        if battery_level is not None:
            payload["battery_level"] = battery_level

        auth_header = f"Bearer {user_jwt}" if user_jwt else f"Bearer {self.backend_jwt}"
        try:
            response = await self.http_client.patch(
                f"/api/omi/devices/{user_id}",
                json=payload,
                headers={"Authorization": auth_header},
            )
            return response.status_code in (200, 204)
        except httpx.RequestError:
            return False

    async def ensure_token_fresh(
        self,
        user_id: str,
        user_jwt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Ensure the stored access token is fresh. Refresh if needed.
        Returns the valid access_token or None if refresh fails.
        """
        data = await self.get_pairing_data(user_id, user_jwt=user_jwt)
        if not data:
            return None

        # Check expiry
        tokens = OmiTokens.from_dict({
            "access_token": data.omi_access_token,
            "refresh_token": data.omi_refresh_token,
            "token_type": "Bearer",
            "expires_in": None,
            "scope": "",
            "uid": data.omi_uid,
            "obtained_at": data.paired_at,  # conservative: use paired_at as base
        })

        # If we have a token_expires_at, check it
        if data.token_expires_at:
            try:
                expires_at = datetime.fromisoformat(data.token_expires_at)
                from datetime import timedelta
                if datetime.now(timezone.utc) >= expires_at - timedelta(seconds=60):
                    if data.omi_refresh_token:
                        logger.info(f"Refreshing expired token for user {user_id}")
                        new_tokens = await self.oauth_client.refresh_tokens(data.omi_refresh_token)
                        # Update stored tokens
                        auth_header = f"Bearer {user_jwt}" if user_jwt else f"Bearer {self.backend_jwt}"
                        await self.http_client.patch(
                            f"/api/omi/devices/{user_id}",
                            json={
                                "omi_access_token": new_tokens.access_token,
                                "omi_refresh_token": new_tokens.refresh_token,
                                "token_expires_at": new_tokens.expires_at.isoformat() if new_tokens.expires_at else None,
                            },
                            headers={"Authorization": auth_header},
                        )
                        return new_tokens.access_token
                    else:
                        logger.warning(f"Token expired for user {user_id} and no refresh token available")
                        return None
            except (ValueError, OmiAuthError) as exc:
                logger.error(f"Token refresh failed for user {user_id}: {exc}")
                return None

        return data.omi_access_token

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _deactivate_device(
        self,
        user_id: str,
        device_id: str,
        user_jwt: Optional[str] = None,
    ) -> bool:
        """Mark a device as inactive (not deleted) in the backend."""
        auth_header = f"Bearer {user_jwt}" if user_jwt else f"Bearer {self.backend_jwt}"
        try:
            response = await self.http_client.patch(
                f"/api/omi/devices/{user_id}",
                json={"is_active": False},
                headers={"Authorization": auth_header},
            )
            return response.status_code in (200, 204)
        except httpx.RequestError:
            return False


class DevicePairingError(Exception):
    """Raised when device pairing operations fail."""
    pass
