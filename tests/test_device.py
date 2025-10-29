import asyncio
import unittest
from unittest.mock import patch

import src.device.example as example_mod


class FakeAdapterAvailable:
    def __init__(self):
        self.available = True

    async def scan(self, timeout=3.0):
        return [{"address": "AA:BB:CC:DD:EE:FF", "name": "mock-device"}]


class FakeAdapterUnavailable:
    def __init__(self):
        self.available = False


class TestDeviceExample(unittest.TestCase):
    def test_run_example_with_mock_available(self):
        async def runner():
            with patch("src.device.example.BLEAdapter", lambda: FakeAdapterAvailable()):
                await example_mod.run_example()

        asyncio.run(runner())

    def test_run_example_with_mock_unavailable(self):
        async def runner():
            with patch("src.device.example.BLEAdapter", lambda: FakeAdapterUnavailable()):
                await example_mod.run_example()

        asyncio.run(runner())


if __name__ == "__main__":
    unittest.main()
