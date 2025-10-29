"""Flipper Zero BLE connection diagnostic script."""

import asyncio
import sys
from bleak import BleakScanner
from typing import Optional

FLIPPER_NAME_PREFIX = "Flipper "  # Flipper Zero devices typically broadcast with this prefix

async def find_flipper() -> Optional[tuple[str, str]]:
    """Scan for Flipper Zero devices."""
    print("Scanning for Flipper Zero devices...")
    
    try:
        devices = await BleakScanner.discover(timeout=5.0)
        
        flipper_devices = [
            (device.address, device.name)
            for device in devices
            if device.name and device.name.startswith(FLIPPER_NAME_PREFIX)
        ]
        
        if not flipper_devices:
            print("\nNo Flipper Zero devices found!")
            print("Please ensure:")
            print("1. Your Flipper Zero is powered on")
            print("2. Bluetooth is enabled on the Flipper (Options -> Bluetooth)")
            print("3. The Flipper is in range")
            print("\nAlternatively, you can:")
            print("1. Connect via USB")
            print("2. Try restarting the Flipper's Bluetooth")
            print("3. Check if the Flipper is already connected to another device")
            return None
            
        print(f"\nFound {len(flipper_devices)} Flipper Zero device(s):")
        for i, (address, name) in enumerate(flipper_devices, 1):
            print(f"{i}. {name} ({address})")
            
        return flipper_devices[0]  # Return the first Flipper found
        
    except Exception as e:
        print(f"\nError during scan: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print("\nTroubleshooting steps:")
        print("1. Check if Windows Bluetooth service is running")
        print("2. Try restarting the Bluetooth adapter")
        print("3. Consider connecting via USB instead")
        raise

async def main():
    """Main entry point."""
    try:
        flipper = await find_flipper()
        if flipper:
            address, name = flipper
            print(f"\nSelected Flipper Zero: {name}")
            print(f"Address: {address}")
            print("\nYou can now use this address to connect using the main application")
            
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())