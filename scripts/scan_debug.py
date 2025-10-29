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
        devices = await BleakScanner.discover(
            timeout=10.0,
            return_adv=True
        )
        
        if not devices:
            print("No devices found! Please check if:")
            print("1. Bluetooth is enabled on your system")
            print("2. The device you're trying to connect to is powered on")
            print("3. You're within range of the device")
            return
            
        print(f"\nFound {len(devices)} devices:")
        for device, adv_data in devices.items():
            print("\nDevice Details:")
            print(f"Address: {device.address}")
            print(f"Name: {device.name or 'Unknown'}")
            print(f"RSSI: {adv_data.rssi} dBm")
            
            if adv_data.manufacturer_data:
                print("Manufacturer Data:")
                for key, value in adv_data.manufacturer_data.items():
                    print(f"  ID: {key}, Data: {value.hex()}")
            
            if adv_data.service_data:
                print("Service Data:")
                for uuid, data in adv_data.service_data.items():
                    print(f"  UUID: {uuid}")
                    print(f"  Data: {data.hex()}")
            
            if adv_data.service_uuids:
                print("Service UUIDs:")
                for uuid in adv_data.service_uuids:
                    print(f"  {uuid}")
                    
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