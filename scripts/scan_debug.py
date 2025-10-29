"""BLE scanning diagnostic script."""

import asyncio
import sys
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

async def scan_devices():
    """Scan for BLE devices and print detailed information."""
    print("Starting BLE scan...")
    print(f"Python version: {sys.version}")
    
    try:
        scanner = BleakScanner()
        devices = await scanner.discover(timeout=10.0)
        
        if not devices:
            print("No devices found! Please check if:")
            print("1. Bluetooth is enabled on your system")
            print("2. The device you're trying to connect to is powered on")
            print("3. You're within range of the device")
            return
            
        print(f"\nFound {len(devices)} devices:")
        for device in devices:
            print("\nDevice Details:")
            print(f"Address: {device.address}")
            print(f"Name: {device.name or 'Unknown'}")
            print(f"Details: {device!r}")
            for attr in dir(device):
                if not attr.startswith('_'):
                    try:
                        value = getattr(device, attr)
                        if not callable(value):
                            print(f"{attr}: {value}")
                    except Exception:
                        continue
                    
    except Exception as e:
        print(f"\nError during scan: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print("\nPlease check:")
        print("1. Bluetooth adapter is working properly")
        print("2. Bluetooth service is running")
        print("3. You have the necessary permissions")
        raise

async def main():
    """Main entry point."""
    try:
        await scan_devices()
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())