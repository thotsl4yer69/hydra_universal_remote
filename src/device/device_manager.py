"""Device manager orchestrating transports and device connectivity."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .flipper_transport import (
    FlipperBLETransport,
    FlipperTransport,
    FlipperUSBTransport,
    TransportStatus,
)

logger = logging.getLogger(__name__)


class ConnectionType(str, Enum):
    USB = "usb"
    BLE = "ble"
    MOCK = "mock"


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class DeviceManager:
    """High-level device orchestration with optional transports."""

    def __init__(self, *, enable_mock: bool = False) -> None:
        transports: Dict[ConnectionType, FlipperTransport] = {
            ConnectionType.USB: FlipperUSBTransport(),
            ConnectionType.BLE: FlipperBLETransport(),
        }

        if enable_mock:
            from .mock_transport import MockTransport
            transports[ConnectionType.MOCK] = MockTransport()

        self._transports = transports
        self._status_callbacks: list[Any] = []
        self.status = ConnectionStatus.DISCONNECTED
        self.connection_type: Optional[ConnectionType] = None
        self.active_transport: Optional[FlipperTransport] = None

    def add_status_callback(self, callback) -> None:
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback) -> None:
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def available_transports(self) -> Dict[ConnectionType, TransportStatus]:
        return {
            conn_type: transport.availability()
            for conn_type, transport in self._transports.items()
        }

    def _update_status(self, status: ConnectionStatus) -> None:
        self.status = status
        for callback in list(self._status_callbacks):
            try:
                callback(status)
            except Exception as exc:  # pragma: no cover - defensive log
                logger.error("Status callback failure: %s", exc)

    async def scan_devices(self) -> Dict[str, Any]:
        devices: Dict[str, Any] = {"usb": None, "ble": None}

        usb_transport = self._transports.get(ConnectionType.USB)
        if usb_transport:
            usb_status = usb_transport.availability()
            if usb_status.available:
                detected = FlipperUSBTransport.find_flipper_port()
                if detected:
                    devices["usb"] = {"port": detected[0], "vid_pid": detected[1]}

        ble_transport = self._transports.get(ConnectionType.BLE)
        if ble_transport:
            ble_status = ble_transport.availability()
            if ble_status.available:
                try:
                    address = await FlipperBLETransport.find_flipper_device()
                    if address:
                        devices["ble"] = {"address": address}
                except Exception as exc:
                    logger.error("BLE scan error: %s", exc)

        return devices

    async def connect(self, connection_type: ConnectionType, **kwargs: Any) -> bool:
        if self.status == ConnectionStatus.CONNECTED:
            await self.disconnect()

        transport = self._transports.get(connection_type)
        if not transport:
            logger.error("Unsupported transport: %s", connection_type)
            return False

        status = transport.availability()
        if not status.available:
            logger.error("Transport %s unavailable: %s", connection_type.value, status.reason)
            self._update_status(ConnectionStatus.ERROR)
            return False

        self._update_status(ConnectionStatus.CONNECTING)

        try:
            success = await transport.connect(**kwargs)
        except Exception as exc:
            logger.error("Connection error via %s: %s", connection_type.value, exc)
            self._update_status(ConnectionStatus.ERROR)
            return False

        if success:
            self.active_transport = transport
            self.connection_type = connection_type
            self._update_status(ConnectionStatus.CONNECTED)
        else:
            self._update_status(ConnectionStatus.ERROR)

        return success

    async def disconnect(self) -> bool:
        if not self.active_transport:
            self._update_status(ConnectionStatus.DISCONNECTED)
            return True

        try:
            await self.active_transport.disconnect()
            return True
        except Exception as exc:
            logger.error("Disconnect error: %s", exc)
            return False
        finally:
            self.active_transport = None
            self.connection_type = None
            self._update_status(ConnectionStatus.DISCONNECTED)

    def is_connected(self) -> bool:
        return self.status == ConnectionStatus.CONNECTED

    async def write(self, data: bytes) -> int:
        if not self.is_connected() or not self.active_transport:
            raise ConnectionError("Device not connected")
        return await self.active_transport.write(data)

    async def read(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        if not self.is_connected() or not self.active_transport:
            raise ConnectionError("Device not connected")
        return await self.active_transport.read(size, timeout)

    def get_connection_info(self) -> Optional[Dict[str, Any]]:
        if not self.is_connected():
            return None
        return {"type": self.connection_type.value if self.connection_type else "unknown", "status": self.status.value}

    async def test_connection(self) -> Tuple[bool, str]:
        if not self.is_connected():
            return False, "Not connected"

        try:
            await self.write(b"ping")
            response = await self.read(timeout=1.0)
            if response:
                return True, f"Received {response!r}"
            return False, "No response"
        except Exception as exc:
            return False, f"Test failed: {exc}"

    async def transmit_signal(self, signal: Any) -> bool:
        """Transmit a prepared signal over the active transport."""
        if not self.is_connected():
            raise ConnectionError("Device not connected")

        payload: Optional[bytes] = None

        # Prefer decoded payloads, fall back to raw data representations.
        candidates = []
        if hasattr(signal, "decoded_data"):
            candidates.append(getattr(signal, "decoded_data"))
        if hasattr(signal, "data"):
            candidates.append(getattr(signal, "data"))
        if hasattr(signal, "raw_samples"):
            raw_samples = getattr(signal, "raw_samples")
            try:
                if raw_samples is not None:
                    if hasattr(raw_samples, "tobytes"):
                        candidates.append(raw_samples.tobytes())
                    elif isinstance(raw_samples, (bytes, bytearray)):
                        candidates.append(bytes(raw_samples))
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.debug("Failed to coerce raw_samples to bytes: %s", exc)

        for candidate in candidates:
            if isinstance(candidate, (bytes, bytearray)) and candidate:
                payload = bytes(candidate)
                break

        if payload is None:
            logger.warning("Signal %s has no payload to transmit", signal)
            return False

        written = await self.write(payload)
        return written == len(payload)