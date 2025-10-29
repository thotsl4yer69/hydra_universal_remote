"""Connection testing utility for Hydra Universal Remote."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import json
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from src.device.device_manager import DeviceManager, ConnectionType, ConnectionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionTester:
    """Tests device connections and reports results."""
    
    def __init__(self):
        """Initialize connection tester."""
        self.device_manager = DeviceManager()
        
    async def scan_and_report(self) -> Dict[str, Any]:
        """Scan for devices and report findings."""
        logger.info("Scanning for devices...")
        
        devices = await self.device_manager.scan_devices()
        
        report = {
            "timestamp": "",  # Will be filled by report_results
            "devices_found": {
                "usb": bool(devices["usb"]),
                "ble": bool(devices["ble"])
            },
            "device_details": devices,
            "connection_tests": {
                "usb": None,
                "ble": None
            }
        }
        
        # Test USB if available
        if devices["usb"]:
            logger.info("Testing USB connection...")
            success = await self.test_usb_connection(devices["usb"]["port"])
            report["connection_tests"]["usb"] = {
                "success": success[0],
                "message": success[1]
            }
            
        # Test BLE if available
        if devices["ble"]:
            logger.info("Testing BLE connection...")
            success = await self.test_ble_connection(devices["ble"]["address"])
            report["connection_tests"]["ble"] = {
                "success": success[0],
                "message": success[1]
            }
            
        return report
        
    async def test_usb_connection(self, port: str) -> tuple[bool, str]:
        """Test USB connection."""
        try:
            success = await self.device_manager.connect(
                ConnectionType.USB,
                port=port
            )
            
            if not success:
                return False, "Failed to establish USB connection"
                
            # Test connection
            test_result = await self.device_manager.test_connection()
            await self.device_manager.disconnect()
            
            return test_result
            
        except Exception as e:
            return False, f"USB test error: {str(e)}"
            
    async def test_ble_connection(self, address: str) -> tuple[bool, str]:
        """Test BLE connection."""
        try:
            success = await self.device_manager.connect(
                ConnectionType.BLE,
                address=address
            )
            
            if not success:
                return False, "Failed to establish BLE connection"
                
            # Test connection
            test_result = await self.device_manager.test_connection()
            await self.device_manager.disconnect()
            
            return test_result
            
        except Exception as e:
            return False, f"BLE test error: {str(e)}"
            
    def report_results(self, results: Dict[str, Any], output_file: Path = None):
        """Generate and optionally save test report."""
        from datetime import datetime
        
        results["timestamp"] = datetime.now().isoformat()
        
        # Print report to console
        print("\n=== Connection Test Report ===")
        print(f"Timestamp: {results['timestamp']}")
        print("\nDevices Found:")
        print(f"  USB: {'Yes' if results['devices_found']['usb'] else 'No'}")
        print(f"  BLE: {'Yes' if results['devices_found']['ble'] else 'No'}")
        
        if results['device_details']['usb']:
            print("\nUSB Device Details:")
            print(f"  Port: {results['device_details']['usb']['port']}")
            print(f"  VID/PID: {results['device_details']['usb']['vid_pid']}")
            
        if results['device_details']['ble']:
            print("\nBLE Device Details:")
            print(f"  Address: {results['device_details']['ble']['address']}")
            
        print("\nConnection Tests:")
        if results['connection_tests']['usb']:
            print("\nUSB Test:")
            print(f"  Success: {results['connection_tests']['usb']['success']}")
            print(f"  Message: {results['connection_tests']['usb']['message']}")
            
        if results['connection_tests']['ble']:
            print("\nBLE Test:")
            print(f"  Success: {results['connection_tests']['ble']['success']}")
            print(f"  Message: {results['connection_tests']['ble']['message']}")
            
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nReport saved to: {output_file}")
            
async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Flipper Zero connections")
    parser.add_argument(
        '--output',
        type=Path,
        help='Save report to file'
    )
    
    args = parser.parse_args()
    
    try:
        tester = ConnectionTester()
        results = await tester.scan_and_report()
        tester.report_results(results, args.output)
        
        # Exit with status based on test results
        usb_success = results['connection_tests']['usb']['success'] if results['connection_tests']['usb'] else False
        ble_success = results['connection_tests']['ble']['success'] if results['connection_tests']['ble'] else False
        
        if not (usb_success or ble_success):
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())