import asyncio
import sys
import platform
from src.device.ble_adapter import BLEAdapter

async def scan_devices():
    # Print system info
    print(f'Python version: {sys.version}')
    print(f'Platform: {platform.platform()}')
    
    adapter = BLEAdapter()
    print(f'\nBLE adapter available: {adapter.available}')
    if not adapter.available:
        print('Bluetooth not available - please ensure bleak is installed and Bluetooth is enabled')
        return
    
    print('\nStarting BLE scan (10 second timeout)...')
    try:
        devices = await adapter.scan(timeout=10.0)
        print(f'\nFound {len(devices)} devices:')
        for device in devices:
            print(f'Address: {device["address"]}, Name: {device["name"]}')
    except Exception as e:
        print(f'\nScan error: {str(e)}')
        print(f'Error type: {type(e).__name__}')
        if hasattr(e, 'winerror'):
            print(f'Windows error code: {e.winerror}')
        import traceback
        print('\nFull error traceback:')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(scan_devices())