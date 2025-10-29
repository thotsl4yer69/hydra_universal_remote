"""Utility functions for working with BLE devices and services."""

import asyncio
from typing import List, Dict, Any, Optional

class BLEDeviceNotFound(Exception):
    """Raised when a BLE device cannot be found."""
    pass

async def scan_for_devices(timeout: float = 5.0) -> List[Dict[str, Any]]:
    """Scan for BLE devices.
    
    Args:
        timeout: How long to scan for devices in seconds
        
    Returns:
        List of discovered devices with their properties
        
    Raises:
        RuntimeError: If BLE scanning fails
    """
    try:
        from bleak import BleakScanner
    except ImportError:
        raise RuntimeError("bleak package is required for BLE functionality")
        
    devices = []
    async with BleakScanner() as scanner:
        devices = await scanner.discover(timeout=timeout)
        
    return [
        {
            "address": dev.address,
            "name": dev.name or "Unknown",
            "rssi": dev.rssi,
            "metadata": dev.metadata
        }
        for dev in devices
    ]

async def connect_device(address: str, timeout: float = 10.0) -> Any:
    """Connect to a BLE device by address.
    
    Args:
        address: Device MAC address or UUID
        timeout: Connection timeout in seconds
        
    Returns:
        Connected BleakClient instance
        
    Raises:
        BLEDeviceNotFound: If device cannot be found/connected
    """
    try:
        from bleak import BleakClient
    except ImportError:
        raise RuntimeError("bleak package is required for BLE functionality")
        
    try:
        client = BleakClient(address)
        await client.connect(timeout=timeout)
        return client
    except Exception as e:
        raise BLEDeviceNotFound(f"Could not connect to device {address}: {str(e)}")

async def list_services(client: Any) -> List[Dict[str, str]]:
    """List services available on connected BLE device.
    
    Args:
        client: Connected BleakClient instance
        
    Returns:
        List of service UUIDs and descriptions
    """
    services = []
    for service in client.services:
        services.append({
            "uuid": service.uuid,
            "description": service.description or "Unknown service"
        })
    return services