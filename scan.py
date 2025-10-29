import asyncio
from src.device.ble_adapter import BLEAdapter

async def scan_devices():
    adapter = BLEAdapter()
    print(f'BLE adapter available: {adapter.available}')
    if not adapter.available:
        print('Bluetooth not available - please ensure bleak is installed and Bluetooth is enabled')
        return
    
    print('Starting BLE scan...')
    try:
        devices = await adapter.scan(timeout=10.0)
        print(f'\nFound {len(devices)} devices:')
        for device in devices:
            print(f'Address: {device["address"]}, Name: {device["name"]}')
    except Exception as e:
        print(f'Scan error: {str(e)}')

if __name__ == '__main__':
    asyncio.run(scan_devices())