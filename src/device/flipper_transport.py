"""Transport helpers for communicating with Flipper Zero over USB or BLE."""

from __future__ import annotations

import asyncio
import logging
import platform
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:  # Optional dependency
    import serial  # type: ignore
    import serial.tools.list_ports  # type: ignore
except Exception:  # pragma: no cover - runtime guard
    serial = None  # type: ignore

try:  # Optional dependency
    from bleak import BleakClient, BleakScanner  # type: ignore
except Exception:  # pragma: no cover - runtime guard
    BleakClient = None  # type: ignore
    BleakScanner = None  # type: ignore

from ..config.flipper_config import FLIPPER_USB_MODES, SERIAL_CONFIG

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransportStatus:
    available: bool
    reason: Optional[str] = None


class FlipperTransport:
    """Transport interface used by the device manager."""

    name: str = "transport"

    @classmethod
    def availability(cls) -> TransportStatus:
        return TransportStatus(True)

    async def connect(self, **kwargs: Any) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    async def disconnect(self) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    async def write(self, data: bytes) -> int:  # pragma: no cover - interface
        raise NotImplementedError

    async def read(self, size: int = -1, timeout: Optional[float] = None) -> bytes:  # pragma: no cover - interface
        raise NotImplementedError


class FlipperUSBTransport(FlipperTransport):
    """Serial transport. Requires pyserial."""

    name = "usb"

    def __init__(self) -> None:
        self.port: Optional[str] = None
        self._serial = None

    @classmethod
    def availability(cls) -> TransportStatus:
        if serial is None:
            return TransportStatus(False, "pyserial not installed")
        return TransportStatus(True)

    @staticmethod
    def find_flipper_port() -> Optional[Tuple[str, Tuple[int, int]]]:
        if serial is None:
            return None

        system = platform.system().lower()
        for port in serial.tools.list_ports.comports():  # type: ignore[attr-defined]
            for _, (vid, pid) in FLIPPER_USB_MODES.items():
                if port.vid == vid and port.pid == pid:
                    if system == "linux":
                        if port.device.startswith("/dev/ttyACM") or port.device.startswith("/dev/ttyUSB"):
                            return port.device, (vid, pid)
                    else:
                        return port.device, (vid, pid)
        return None

    async def connect(self, **kwargs: Any) -> bool:
        if serial is None:
            logger.warning("USB transport unavailable: pyserial missing")
            return False

        port = kwargs.get("port") or self.port
        if not port:
            detected = self.find_flipper_port()
            if not detected:
                logger.error("No Flipper Zero device detected on USB")
                return False
            port, _ = detected

        try:
            self._serial = serial.Serial(port=port, **SERIAL_CONFIG)  # type: ignore[attr-defined]
            self.port = port
            await asyncio.sleep(0.05)
            return True
        except Exception as exc:  # serial.SerialException or others
            logger.error("USB connection failed: %s", exc)
            if platform.system().lower() == "linux":
                logger.info("Ensure the user is in the 'dialout' group or check udev rules.")
            self._serial = None
            return False

    async def disconnect(self) -> bool:
        if not self._serial:
            return True
        try:
            self._serial.close()
            return True
        except Exception as exc:  # serial.SerialException
            logger.error("USB disconnect failed: %s", exc)
            return False
        finally:
            self._serial = None

    async def write(self, data: bytes) -> int:
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("USB transport not connected")
        return self._serial.write(data)

    async def read(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("USB transport not connected")

        original_timeout = self._serial.timeout
        try:
            if timeout is not None:
                self._serial.timeout = timeout
            return self._serial.read(size)
        finally:
            if timeout is not None:
                self._serial.timeout = original_timeout


class FlipperBLETransport(FlipperTransport):
    """BLE transport. Requires bleak."""

    name = "ble"
    SERVICE_UUID = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0000"
    RX_CHAR_UUID = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0002"
    TX_CHAR_UUID = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0003"

    def __init__(self) -> None:
        self.address: Optional[str] = None
        self._client = None
        self._notification_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._rx_char_uuid: Optional[str] = None
        self._tx_char_uuid: Optional[str] = None

    @classmethod
    def availability(cls) -> TransportStatus:
        if BleakClient is None or BleakScanner is None:
            return TransportStatus(False, "bleak not installed")
        return TransportStatus(True)

    @staticmethod
    async def find_flipper_device() -> Optional[str]:
        if BleakScanner is None:
            return None
        try:
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name and "Flipper" in device.name:
                    return device.address
        except Exception as exc:
            logger.error("BLE scan failed: %s", exc)
        return None

    def _notification_handler(self, _: str, data: bytearray) -> None:
        self._notification_queue.put_nowait(bytes(data))

    async def connect(self, **kwargs: Any) -> bool:
        if BleakClient is None:
            logger.warning("BLE transport unavailable: bleak missing")
            return False

        address = kwargs.get("address") or self.address
        if not address:
            address = await self.find_flipper_device()
            if not address:
                logger.error("No Flipper Zero detected via BLE")
                return False

        try:
            client = BleakClient(address)
            await client.connect()
            self.address = address
            self._client = client

            if client.services is None:
                await client.get_services()

            target_rx = self.RX_CHAR_UUID.lower()
            target_tx = self.TX_CHAR_UUID.lower()

            for service in client.services:
                for characteristic in service.characteristics:
                    uuid = characteristic.uuid.lower()
                    if uuid == target_rx:
                        self._rx_char_uuid = characteristic.uuid
                    elif uuid == target_tx:
                        self._tx_char_uuid = characteristic.uuid

            if not self._rx_char_uuid or not self._tx_char_uuid:
                logger.error("Required BLE characteristics not found on device")
                await client.disconnect()
                self._client = None
                return False

            await client.start_notify(self._rx_char_uuid, self._notification_handler)
            return True
        except Exception as exc:
            logger.error("BLE connection failed: %s", exc)
            self._client = None
            return False

    async def disconnect(self) -> bool:
        if not self._client:
            return True
        try:
            await self._client.disconnect()
            return True
        except Exception as exc:
            logger.error("BLE disconnect failed: %s", exc)
            return False
        finally:
            self._client = None

    async def write(self, data: bytes) -> int:
        if not self._client or not self._client.is_connected:
            raise ConnectionError("BLE transport not connected")
        assert self._tx_char_uuid
        await self._client.write_gatt_char(self._tx_char_uuid, data)
        return len(data)

    async def read(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        if not self._client or not self._client.is_connected:
            raise ConnectionError("BLE transport not connected")
        try:
            return await asyncio.wait_for(self._notification_queue.get(), timeout)
        except asyncio.TimeoutError:
            return b""
