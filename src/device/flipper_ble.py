"""Flipper Zero specific BLE adapter."""

from typing import List, Dict, Any, Optional
import logging
from .ble_adapter import BLEAdapter

logger = logging.getLogger(__name__)

class FlipperZeroBLE(BLEAdapter):
    """Flipper Zero-specific BLE adapter with custom functionality."""
    
    FLIPPER_NAME_PREFIX = "Flipper "
    
    def __init__(self):
        """Initialize the Flipper Zero BLE adapter."""
        super().__init__()
        self._device_info = None
        
    @staticmethod
    def is_flipper_device(name: Optional[str]) -> bool:
        """Check if a device name matches Flipper Zero pattern."""
        return bool(name and name.startswith(FlipperZeroBLE.FLIPPER_NAME_PREFIX))
    
    async def find_flipper(self) -> Optional[Dict[str, Any]]:
        """Scan specifically for Flipper Zero devices."""
        try:
            devices = await self.scan(timeout=5.0)
            for device in devices:
                if self.is_flipper_device(device.get("name")):
                    return device
            return None
        except Exception as e:
            logger.error(f"Error finding Flipper Zero: {e}")
            return None
    
    async def connect_to_flipper(self, address: Optional[str] = None) -> bool:
        """Connect to a Flipper Zero device.
        
        If address is not provided, will scan for available Flippers.
        """
        try:
            if not address:
                device = await self.find_flipper()
                if not device:
                    logger.error("No Flipper Zero found during scan")
                    return False
                address = device.get("address")
            
            if not address:
                logger.error("No valid Flipper Zero address available")
                return False
                
            connected = await self.connect(address)
            if connected:
                logger.info(f"Connected to Flipper Zero at {address}")
                self._device_info = {"address": address}
            return connected
            
        except Exception as e:
            logger.error(f"Error connecting to Flipper Zero: {e}")
            return False
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the connected Flipper Zero."""
        return self._device_info if self.is_connected() else None