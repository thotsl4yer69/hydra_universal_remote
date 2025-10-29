import asyncio
import logging
from src.device.flipper_ble import FlipperZeroBLE

logging.basicConfig(level=logging.INFO)

async def main():
    flipper = FlipperZeroBLE()
    
    print("Scanning for Flipper Zero...")
    device = await flipper.find_flipper()
    
    if not device:
        print("No Flipper Zero found!")
        return
        
    print(f"Found Flipper Zero: {device.get('name')} at {device.get('address')}")
    print("Attempting to connect...")
    
    if await flipper.connect_to_flipper(device.get('address')):
        print("Successfully connected!")
        print("Device info:", flipper.get_device_info())
        
        # Send a test command (simple ping)
        test_command = b'\x01'  # Simple ping command
        if await flipper.send_command(test_command):
            print("Test command sent successfully")
            response = await flipper.read_response()
            if response:
                print(f"Received response: {response.hex()}")
        
        await flipper.disconnect()
        print("Disconnected")
    else:
        print("Failed to connect!")

if __name__ == "__main__":
    asyncio.run(main())