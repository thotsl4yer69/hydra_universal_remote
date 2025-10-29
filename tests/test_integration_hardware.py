import os
import asyncio
import unittest

from src.device.ble_adapter import BLEAdapter, BLENotAvailable


@unittest.skipUnless(
    os.environ.get("RUN_HARDWARE_INTEGRATION") == "true",
    "Hardware integration tests are disabled (set RUN_HARDWARE_INTEGRATION=true to enable)",
)
class TestHardwareIntegration(unittest.TestCase):
    def test_ble_scan_returns_list(self):
        adapter = BLEAdapter()
        # Ensure bleak is available in the environment where this runs
        self.assertTrue(adapter.available, "bleak must be installed for hardware integration tests")

        # If the BLE backend can't start (no adapter, permissions, etc.),
        # treat this as an environment limitation and skip the test instead
        # of failing the suite.
        try:
            devices = asyncio.run(adapter.scan(timeout=5.0))
        except BLENotAvailable:
            self.skipTest("bleak not available in this environment")
        except OSError as exc:
            # WinError -2147020577 and similar indicate the Bluetooth
            # device/driver/service isn't ready — skip the integration test.
            self.skipTest(f"Bluetooth hardware not ready: {exc}")

        self.assertIsInstance(devices, list)


if __name__ == "__main__":
    unittest.main()
