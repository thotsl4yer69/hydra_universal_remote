import asyncio
from .ble_adapter import BLEAdapter, BLENotAvailable


async def run_example():
    adapter = BLEAdapter()
    print(f"BLE adapter available: {adapter.available}")
    if not adapter.available:
        print("bleak not available — install bleak in a supported Python version to test hardware")
        return
    try:
        devices = await adapter.scan(timeout=3.0)
        print(f"found {len(devices)} devices")
        for d in devices[:10]:
            print(d)
    except BLENotAvailable:
        print("bleak is not usable in this environment")


if __name__ == "__main__":
    asyncio.run(run_example())
