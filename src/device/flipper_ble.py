"""Flipper Zero specific BLE adapter."""

from typing import List, Dict, Any, Optional
import logging
from .ble_adapter import BLEAdapter

logger = logging.getLogger(__name__)

class FlipperZeroBLE(BLEAdapter):
    """Flipper Zero-specific BLE adapter with custom functionality."""
    
    FLIPPER_NAME_PREFIX = "Flipper "
    
    # Flipper Zero BLE Service UUIDs
    SERVICE_UUID = "00001800-0000-1000-8000-00805f9b34fb"  # Generic Access Service
    SERIAL_SERVICE_UUID = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0000"  # Flipper Serial Service
    
    # Characteristic UUIDs
    RX_CHAR_UUID = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0002"  # Read from Flipper
    TX_CHAR_UUID = "8fe5b3d5-2e7f-4a98-2a48-7acc60fe0003"  # Write to Flipper
    
    def __init__(self):
        """Initialize the Flipper Zero BLE adapter."""
        super().__init__()
        self._device_info = None
        self._rx_characteristic = None
        self._tx_characteristic = None
    
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
        """Connect to a Flipper Zero device with proper service discovery."""
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
            if not connected:
                return False
                
            # Get Flipper's Serial Service
            services = await self.get_services()
            serial_service = next(
                (service for service in services 
                 if service.uuid.lower() == self.SERIAL_SERVICE_UUID.lower()),
                None
            )
            
            if not serial_service:
                logger.error("Flipper Zero Serial Service not found")
                await self.disconnect()
                return False
                
            # Get RX/TX characteristics
            for char in serial_service.characteristics:
                if char.uuid.lower() == self.RX_CHAR_UUID.lower():
                    self._rx_characteristic = char
                elif char.uuid.lower() == self.TX_CHAR_UUID.lower():
                    self._tx_characteristic = char
                    
            if not (self._rx_characteristic and self._tx_characteristic):
                logger.error("Required characteristics not found")
                await self.disconnect()
                return False
                
            logger.info(f"Successfully connected to Flipper Zero at {address}")
            self._device_info = {"address": address}
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Flipper Zero: {e}")
            await self.disconnect()
            return False
    
    async def send_command(self, command: bytes) -> bool:
        """Send a command to the Flipper Zero."""
        try:
            if not self.is_connected() or not self._tx_characteristic:
                logger.error("Not connected to Flipper Zero")
                return False
                
            await self.write_characteristic(
                self._tx_characteristic.uuid,
                command
            )
            return True
        except Exception as e:
            logger.error(f"Error sending command to Flipper Zero: {e}")
            return False
    
    async def read_response(self) -> Optional[bytes]:
        """Read response from the Flipper Zero."""
        try:
            if not self.is_connected() or not self._rx_characteristic:
                logger.error("Not connected to Flipper Zero")
                return None
                
            return await self.read_characteristic(
                self._rx_characteristic.uuid
            )
        except Exception as e:
            logger.error(f"Error reading from Flipper Zero: {e}")
            return None
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the connected Flipper Zero."""
        return self._device_info if self.is_connected() else None