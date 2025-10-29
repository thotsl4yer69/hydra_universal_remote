import os
import asyncio
import unittest

from src.device.ble_adapter import BLEAdapter


@unittest.skipUnless(
    os.environ.get("RUN_HARDWARE_INTEGRATION") == "true",
    "Hardware integration tests are disabled (set RUN_HARDWARE_INTEGRATION=true to enable)",
)
class TestHardwareIntegration(unittest.TestCase):
    def test_ble_scan_returns_list(self):
        adapter = BLEAdapter()
        # Ensure bleak is available in the environment where this runs
        self.assertTrue(adapter.available, "bleak must be installed for hardware integration tests")

        devices = asyncio.run(adapter.scan(timeout=5.0))
        self.assertIsInstance(devices, list)


if __name__ == "__main__":
    unittest.main()
