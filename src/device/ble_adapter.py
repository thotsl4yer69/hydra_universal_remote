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

            self._BleakScanner = BleakScanner
            self._available = True
        except Exception:
            self._BleakScanner = None
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
