"""Unit tests for the BLEAdapter class focusing on error handling."""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import sys

from src.device.ble_adapter import BLEAdapter, BLENotAvailable

class TestBLEAdapter(unittest.TestCase):
    """Test BLEAdapter initialization and error handling."""
    
    def test_init_bleak_not_available(self):
        """Test BLEAdapter initialization when bleak cannot be imported."""
        with patch.dict(sys.modules, {'bleak': None}):
            adapter = BLEAdapter()
            self.assertFalse(adapter.available)
    
    def test_init_bleak_import_error(self):
        """Test BLEAdapter handles arbitrary errors during bleak import."""
        with patch.dict(sys.modules, {'bleak': None}):
            adapter = BLEAdapter()
            self.assertFalse(adapter.available)
    
    def test_init_bleak_success(self):
        """Test BLEAdapter successful initialization."""
        with patch('bleak.BleakScanner'):
            adapter = BLEAdapter()
            self.assertTrue(adapter.available)
    
    async def async_scan_error(self):
        """Test BLEAdapter scan when backend raises an error."""
        mock_scanner_class = AsyncMock()
        mock_scanner_class.discover = AsyncMock(side_effect=OSError("Mock hardware error"))
        
        with patch('bleak.BleakScanner', mock_scanner_class):
            adapter = BLEAdapter()
            with self.assertRaises(OSError):
                await adapter.scan()
    
    def test_scan_error(self):
        """Run async test for scan error."""
        asyncio.run(self.async_scan_error())
    
    async def async_scan_not_available(self):
        """Test BLEAdapter scan when bleak is not available."""
        with patch.dict(sys.modules, {'bleak': None}):
            adapter = BLEAdapter()
            with self.assertRaises(BLENotAvailable):
                await adapter.scan()
    
    def test_scan_not_available(self):
        """Run async test for unavailable scanner."""
        asyncio.run(self.async_scan_not_available())
    
    async def async_scan_success(self):
        """Test successful BLE scan with mock device."""
        mock_device = MagicMock()
        mock_device.address = "00:11:22:33:44:55"
        mock_device.name = "Test Device"
        
        mock_scanner_class = AsyncMock()
        mock_scanner_class.discover = AsyncMock(return_value=[mock_device])
        
        with patch('bleak.BleakScanner', mock_scanner_class):
            adapter = BLEAdapter()
            devices = await adapter.scan()
            
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["address"], "00:11:22:33:44:55")  
            self.assertEqual(devices[0]["name"], "Test Device")
    
    def test_scan_success(self):
        """Run async test for successful scan."""
        asyncio.run(self.async_scan_success())

if __name__ == '__main__':
    unittest.main()