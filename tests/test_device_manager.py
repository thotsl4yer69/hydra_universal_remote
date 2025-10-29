import asyncio
import unittest

from src.device.device_manager import DeviceManager, ConnectionType


class DummySignal:
    def __init__(self, payload: bytes):
        self.decoded_data = payload
        self.data = None
        self.raw_samples = None


class DummySignalNoPayload:
    decoded_data = None
    data = None
    raw_samples = None


class TestDeviceManagerTransmit(unittest.TestCase):
    def test_transmit_signal_with_mock_transport(self):
        async def runner():
            manager = DeviceManager(enable_mock=True)
            self.assertTrue(await manager.connect(ConnectionType.MOCK))
            signal = DummySignal(b"payload")
            result = await manager.transmit_signal(signal)
            await manager.disconnect()
            return result

        self.assertTrue(asyncio.run(runner()))

    def test_transmit_signal_without_payload(self):
        async def runner():
            manager = DeviceManager(enable_mock=True)
            self.assertTrue(await manager.connect(ConnectionType.MOCK))
            signal = DummySignalNoPayload()
            result = await manager.transmit_signal(signal)
            await manager.disconnect()
            return result

        self.assertFalse(asyncio.run(runner()))


if __name__ == "__main__":
    unittest.main()
