"""
Bluetooth pairing flow for Omi wearable device.

Omi devices advertise over BLE. This module handles:
- Device discovery via BLE scan
- Identifying Omi devices by their advertised service UUID
- Pairing initiation (PIN-free, uses BLE bonding)

NOTE: In V1, Bluetooth pairing is expected to happen via the Omi mobile app.
This module provides the server-side counterpart: verifying device identity
once the user completes BLE pairing on their phone, and confirming the
device serial/ID that will be linked to their user_id in our backend.

Bluetooth scanning uses `bleak` (cross-platform BLE library).
Install: pip install bleak
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Omi BLE service UUID — identified from Omi firmware/hardware open-source code
OMI_BLE_SERVICE_UUID = "19b10000-e8f2-537e-4f6c-d104768a1214"

# Fallback: also look for devices advertising "OMI" or "Friend" in the name
OMI_DEVICE_NAME_PREFIXES = ("OMI", "Friend", "Omi")


@dataclass
class DiscoveredDevice:
    """A discovered Omi BLE device."""
    address: str
    name: str
    rssi: int
    service_uuids: list[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_omi_device(self) -> bool:
        """Check if this looks like an Omi device."""
        # Check by service UUID (most reliable)
        if any(OMI_BLE_SERVICE_UUID.lower() in u.lower() for u in self.service_uuids):
            return True
        # Fallback: check device name
        if self.name and any(
            self.name.startswith(prefix) for prefix in OMI_DEVICE_NAME_PREFIXES
        ):
            return True
        return False


class BluetoothPairer:
    """
    Handles Omi BLE device discovery and pairing verification.

    In production, the mobile app handles the physical BLE pairing.
    This class is used to:
    1. Discover nearby Omi devices (for the pairing UI flow)
    2. Verify a device address claimed by the mobile app is a real Omi device
    3. Extract the device serial number from BLE advertisements
    """

    def __init__(self, scan_timeout: float = 10.0):
        self.scan_timeout = scan_timeout
        self._bleak_available = self._check_bleak()

    def _check_bleak(self) -> bool:
        try:
            import bleak  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "bleak not installed — BLE scanning disabled. "
                "Install with: pip install bleak"
            )
            return False

    async def scan_for_omi_devices(self) -> list[DiscoveredDevice]:
        """
        Scan for nearby Omi BLE devices.

        Returns a list of discovered Omi devices, sorted by signal strength (RSSI).
        Strongest signal first (most likely the user's own device).
        """
        if not self._bleak_available:
            logger.warning("BLE scanning not available — returning empty device list")
            return []

        from bleak import BleakScanner

        discovered = []

        logger.info(f"Starting BLE scan for {self.scan_timeout}s...")

        try:
            devices = await BleakScanner.discover(timeout=self.scan_timeout)
        except Exception as exc:
            logger.error(f"BLE scan failed: {exc}")
            return []

        for device in devices:
            advertisement = getattr(device, "details", {})
            # bleak exposes service UUIDs via metadata
            service_uuids = list(getattr(device, "metadata", {}).get("uuids", []))

            discovered_device = DiscoveredDevice(
                address=device.address,
                name=device.name or "",
                rssi=device.rssi or -100,
                service_uuids=service_uuids,
            )

            if discovered_device.is_omi_device:
                logger.info(
                    f"Found Omi device: {discovered_device.name} "
                    f"({discovered_device.address}) RSSI={discovered_device.rssi}"
                )
                discovered.append(discovered_device)

        # Sort by RSSI descending (stronger signal = closer device)
        discovered.sort(key=lambda d: d.rssi, reverse=True)
        logger.info(f"Found {len(discovered)} Omi device(s)")
        return discovered

    async def verify_device_address(self, address: str) -> Optional[DiscoveredDevice]:
        """
        Verify that a claimed device address is a real, nearby Omi device.
        Used after mobile app reports a successful pairing.

        Returns the DiscoveredDevice if verified, None otherwise.
        """
        devices = await self.scan_for_omi_devices()
        for device in devices:
            if device.address.lower() == address.lower():
                return device
        return None

    def parse_device_id_from_address(self, ble_address: str) -> str:
        """
        Derive a stable device_id from the BLE MAC address.
        Normalizes the address to lowercase, strips colons.

        Example: "AA:BB:CC:DD:EE:FF" -> "aabbccddeeff"
        """
        return ble_address.lower().replace(":", "").replace("-", "")


def scan_devices_sync(timeout: float = 10.0) -> list[DiscoveredDevice]:
    """Synchronous wrapper for BLE scanning (for use in non-async contexts)."""
    pairer = BluetoothPairer(scan_timeout=timeout)
    return asyncio.run(pairer.scan_for_omi_devices())
