from typing import List, Dict, Any


class BLENotAvailable(RuntimeError):
    pass


class BLEAdapter:
    """A minimal BLE adapter wrapper.

    - Uses `bleak` if available.
    - Exposes small, testable async methods (scan/connect) that can be
      mocked in unit tests.
    """

    def __init__(self):
        try:
            from bleak import BleakScanner  # type: ignore
            from bleak import BleakClient  # type: ignore

            self._BleakScanner = BleakScanner
            self._BleakClient = BleakClient
            self._available = True
            self._client = None
        except Exception:
            self._BleakScanner = None
            self._BleakClient = None
            self._client = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def scan(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        """Scan for nearby BLE devices and return simplified dicts.

        If `bleak` is not available this raises `BLENotAvailable`.
        """
        if not self._available:
            raise BLENotAvailable("bleak is not installed or not usable in this environment")

        scanner = self._BleakScanner
        devices = await scanner.discover(timeout=timeout)
        result: List[Dict[str, Any]] = []
        for d in devices:
            result.append({"address": getattr(d, "address", None), "name": getattr(d, "name", None)})
        return result

    async def connect(self, address: str, timeout: float = 10.0) -> bool:
        """Connect to a BLE device by address."""
        if not self._available or self._BleakClient is None:
            raise BLENotAvailable("bleak is not installed or not usable in this environment")
        self._client = self._BleakClient(address)
        try:
            await self._client.connect(timeout=timeout)
            return self._client.is_connected
        except Exception as e:
            self._client = None
            raise e

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    def is_connected(self) -> bool:
        """Return connection state."""
        return self._client is not None and getattr(self._client, "is_connected", False)

    async def read_characteristic(self, char_uuid: str) -> bytes:
        """Read a BLE characteristic by UUID."""
        if self._client is None or not self.is_connected():
            raise RuntimeError("Not connected to any BLE device")
        return await self._client.read_gatt_char(char_uuid)

    async def write_characteristic(self, char_uuid: str, data: bytes) -> None:
        """Write to a BLE characteristic by UUID."""
        if self._client is None or not self.is_connected():
            raise RuntimeError("Not connected to any BLE device")
        await self._client.write_gatt_char(char_uuid, data)
