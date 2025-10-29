"""
Flipper Zero transport implementations.
Handles USB and BLE connections with automatic protocol detection for Windows, Linux, and Pi.
"""

import serial
import serial.tools.list_ports
from bleak import BleakClient, BleakScanner
from typing import Optional, Tuple, Dict, Any
import platform
from ..config.flipper_config import FLIPPER_USB_MODES, SERIAL_CONFIG
import asyncio
import logging

logger = logging.getLogger(__name__)

class FlipperTransport:
    async def connect(self) -> bool:
        raise NotImplementedError
    async def disconnect(self) -> bool:
        raise NotImplementedError
    async def write(self, data: bytes) -> int:
        raise NotImplementedError
    async def read(self, size: int = -1, timeout: float = None) -> bytes:
        raise NotImplementedError

class FlipperUSBTransport(FlipperTransport):
    def __init__(self, port: Optional[str] = None):
        self.port = port
        self._serial = None
        self._mode = None
    @staticmethod
    def find_flipper_port() -> Optional[Tuple[str, Tuple[int, int]]]:
        system = platform.system().lower()
        for port in serial.tools.list_ports.comports():
            for mode, (vid, pid) in FLIPPER_USB_MODES.items():
                if port.vid == vid and port.pid == pid:
                    if system == "linux":
                        if port.device.startswith("/dev/ttyACM") or port.device.startswith("/dev/ttyUSB"):
                            return port.device, (vid, pid)
                    else:
                        return port.device, (vid, pid)
        return None
    async def connect(self) -> bool:
        if not self.port:
            port_info = self.find_flipper_port()
            if not port_info:
                logger.error("No Flipper Zero device found")
                return False
            self.port = port_info[0]
        try:
            self._serial = serial.Serial(port=self.port, **SERIAL_CONFIG)
            await asyncio.sleep(0.1)
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect: {e}")
            if platform.system().lower() == "linux":
                logger.error("Try adding your user to the 'dialout' group or check udev rules for serial access.")
            return False
    async def disconnect(self) -> bool:
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                return True
            except serial.SerialException as e:
                logger.error(f"Error disconnecting: {e}")
                return False
        return True
    async def write(self, data: bytes) -> int:
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Not connected")
        try:
            return self._serial.write(data)
        except serial.SerialException as e:
            logger.error(f"Write error: {e}")
            raise
    async def read(self, size: int = -1, timeout: float = None) -> bytes:
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Not connected")
        original_timeout = self._serial.timeout
        try:
            if timeout is not None:
                self._serial.timeout = timeout
            data = self._serial.read(size)
            return data
        except serial.SerialException as e:
            logger.error(f"Read error: {e}")
            raise
        finally:
            if timeout is not None:
                self._serial.timeout = original_timeout

class FlipperBLETransport(FlipperTransport):
    SERVICE_UUID = "00001800-0000-1000-8000-00805f9b34fb"
    RX_CHAR_UUID = "00002902-0000-1000-8000-00805f9b34fb"
    TX_CHAR_UUID = "00002901-0000-1000-8000-00805f9b34fb"
    def __init__(self, address: Optional[str] = None):
        self.address = address
        self._client = None
        self._rx_char = None
        self._tx_char = None
        self._notification_queue = asyncio.Queue()
    @staticmethod
    async def find_flipper_device() -> Optional[str]:
        try:
            scanner = BleakScanner()
            devices = await scanner.discover()
            for device in devices:
                if device.name and "Flipper" in device.name:
                    return device.address
            return None
        except Exception as e:
            logger.error(f"BLE scan error: {e}")
            return None
    def _notification_handler(self, _, data: bytearray):
        self._notification_queue.put_nowait(bytes(data))
    async def connect(self) -> bool:
        if not self.address:
            self.address = await self.find_flipper_device()
            if not self.address:
                logger.error("No Flipper Zero BLE device found")
                return False
        try:
            self._client = BleakClient(self.address)
            await self._client.connect()
            for service in self._client.services:
                for char in service.characteristics:
                    if char.uuid == self.RX_CHAR_UUID:
                        self._rx_char = char
                    elif char.uuid == self.TX_CHAR_UUID:
                        self._tx_char = char
            if not self._rx_char or not self._tx_char:
                logger.error("Required BLE characteristics not found")
                await self.disconnect()
                return False
            await self._client.start_notify(
                self._rx_char.uuid,
                self._notification_handler
            )
            return True
        except Exception as e:
            logger.error(f"BLE connection error: {e}")
            return False
    async def disconnect(self) -> bool:
        if self._client:
            try:
                await self._client.disconnect()
                return True
            except Exception as e:
                logger.error(f"BLE disconnect error: {e}")
                return False
        return True
    async def write(self, data: bytes) -> int:
        if not self._client or not self._client.is_connected:
            raise ConnectionError("Not connected")
        try:
            await self._client.write_gatt_char(self._tx_char.uuid, data)
            return len(data)
        except Exception as e:
            logger.error(f"BLE write error: {e}")
            raise
    async def read(self, size: int = -1, timeout: float = None) -> bytes:
        if not self._client or not self._client.is_connected:
            raise ConnectionError("Not connected")
        try:
            return await asyncio.wait_for(
                self._notification_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return b''
