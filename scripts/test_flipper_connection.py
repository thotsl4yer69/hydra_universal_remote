"""Test Flipper Zero BLE connection."""

import asyncio
import logging
from src.device.flipper_ble import FlipperZeroBLE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test Flipper Zero BLE connection."""
    flipper = FlipperZeroBLE()
    
    try:
        # Connect to the specific Flipper Zero we found
        FLIPPER_ADDRESS = "80:E1:26:5E:6F:08"  # Your Flipper's address from the scan
        logger.info(f"Attempting to connect to Flipper Zero at {FLIPPER_ADDRESS}...")
        connected = await flipper.connect_to_flipper(FLIPPER_ADDRESS)
        
        if connected:
            logger.info("Successfully connected to Flipper Zero!")
            device_info = flipper.get_device_info()
            logger.info(f"Device info: {device_info}")
            
            # Keep connection alive briefly
            await asyncio.sleep(5)
            
            # Disconnect
            logger.info("Disconnecting...")
            await flipper.disconnect()
            logger.info("Disconnected.")
        else:
            logger.error("Failed to connect to Flipper Zero")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        if flipper.is_connected():
            await flipper.disconnect()

if __name__ == "__main__":
    asyncio.run(main())