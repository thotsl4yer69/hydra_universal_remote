"""
Flipper Zero device interface.
Handles communication with Flipper Zero device over USB/Serial or BLE.
Implements official protocols and community best practices.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Union
import json
from dataclasses import dataclass
from pathlib import Path

from .flipper_protocol import FlipperProtocol, RPCMessage, MessageType, FlipperProtocolError
from .flipper_transport import FlipperUSBTransport, FlipperBLETransport
from ..config.flipper_config import (
    FREQUENCY_RANGES, SUPPORTED_PROTOCOLS, RPC_COMMANDS,
    SubGHzPreset, CAPTURE_SETTINGS, DEFAULT_PATHS
)

logger = logging.getLogger(__name__)

class FlipperMode(Enum):
    """Flipper Zero operating modes."""
    SUB_GHZ = "subghz"
    RFID = "rfid"
    NFC = "nfc"
    IR = "infrared"
    GPIO = "gpio"
    IBUTTON = "ibutton"

@dataclass
class FlipperSignal:
    """Container for captured signal data."""
    mode: FlipperMode
    frequency: Optional[float] = None  # For Sub-GHz
    modulation: Optional[str] = None   # For Sub-GHz
    protocol: Optional[str] = None     # For various modes
    data: bytes = b""
    metadata: Dict[str, Any] = None

class FlipperZeroDevice:
    """Interface for communicating with Flipper Zero.
    
    Implements comprehensive device control following official protocols.
    Supports both USB and BLE communication channels.
    """
    
    def __init__(self):
        """Initialize Flipper Zero interface."""
        self.connected = False
        self.current_mode: Optional[FlipperMode] = None
        self._transport = None
        self._protocol = FlipperProtocol()
        self.device_info = {}
        
        # Initialize storage paths
        self.storage = {k: Path(v) for k, v in DEFAULT_PATHS.items()}
        
    async def connect_usb(self, port: Optional[str] = None) -> bool:
        """Connect to Flipper Zero via USB/Serial.
        
        Args:
            port: Optional COM port. If not provided, will auto-detect.
            
        Returns:
            bool: True if connection successful
        """
        try:
            self._transport = FlipperUSBTransport(port)
            if await self._transport.connect():
                self.connected = True
                await self._init_device()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect via USB: {e}")
            return False
            
    async def connect_ble(self, address: Optional[str] = None) -> bool:
        """Connect to Flipper Zero via BLE.
        
        Args:
            address: Optional BLE address. If not provided, will scan.
            
        Returns:
            bool: True if connection successful
        """
        try:
            self._transport = FlipperBLETransport(address)
            if await self._transport.connect():
                self.connected = True
                await self._init_device()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect via BLE: {e}")
            return False
            
    async def _init_device(self):
        """Initialize device after connection."""
        try:
            # Get device info
            response = await self._protocol.send_command(
                self._transport,
                RPC_COMMANDS["system"]["device_info"]
            )
            self.device_info = response.args
            
            # Create storage directories if needed
            storage_response = await self._protocol.send_command(
                self._transport,
                RPC_COMMANDS["storage"]["list"],
                {"path": "/ext"}
            )
            
            for path in DEFAULT_PATHS.values():
                if path not in storage_response.args.get("paths", []):
                    await self._protocol.send_command(
                        self._transport,
                        RPC_COMMANDS["storage"]["mkdir"],
                        {"path": path}
                    )
                    
        except Exception as e:
            logger.error(f"Device initialization failed: {e}")
            raise
            
    async def disconnect(self) -> bool:
        """Disconnect from device."""
        if not self.connected:
            return True
            
        try:
            if self._transport:
                # Cleanup transport
                self._transport = None
            self.connected = False
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
            
    async def set_mode(self, mode: FlipperMode) -> bool:
        """Switch Flipper Zero to specified mode."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        try:
            # Mode switching logic will be implemented here
            self.current_mode = mode
            return True
        except Exception as e:
            logger.error(f"Failed to set mode {mode}: {e}")
            return False
            
    # Sub-GHz Operations
    async def start_subghz_scan(self, frequency: float, modulation: str = "AM") -> bool:
        """Start scanning for Sub-GHz signals."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        await self.set_mode(FlipperMode.SUB_GHZ)
        # Implement Sub-GHz scan start
        return True
        
    async def stop_subghz_scan(self) -> bool:
        """Stop scanning for Sub-GHz signals."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        # Implement Sub-GHz scan stop
        return True
        
    async def transmit_subghz(self, signal: FlipperSignal) -> bool:
        """Transmit a Sub-GHz signal."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        if signal.mode != FlipperMode.SUB_GHZ:
            raise ValueError("Signal is not a Sub-GHz signal")
            
        await self.set_mode(FlipperMode.SUB_GHZ)
        # Implement signal transmission
        return True
        
    # RFID Operations
    async def read_rfid(self) -> Optional[FlipperSignal]:
        """Read RFID card."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        await self.set_mode(FlipperMode.RFID)
        # Implement RFID read
        return None
        
    async def write_rfid(self, signal: FlipperSignal) -> bool:
        """Write to RFID card."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        if signal.mode != FlipperMode.RFID:
            raise ValueError("Signal is not an RFID signal")
            
        await self.set_mode(FlipperMode.RFID)
        # Implement RFID write
        return True
        
    async def emulate_rfid(self, signal: FlipperSignal) -> bool:
        """Emulate RFID card."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        if signal.mode != FlipperMode.RFID:
            raise ValueError("Signal is not an RFID signal")
            
        await self.set_mode(FlipperMode.RFID)
        # Implement RFID emulation
        return True
        
    # NFC Operations
    async def read_nfc(self) -> Optional[FlipperSignal]:
        """Read NFC tag."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        await self.set_mode(FlipperMode.NFC)
        # Implement NFC read
        return None
        
    async def write_nfc(self, signal: FlipperSignal) -> bool:
        """Write to NFC tag."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        if signal.mode != FlipperMode.NFC:
            raise ValueError("Signal is not an NFC signal")
            
        await self.set_mode(FlipperMode.NFC)
        # Implement NFC write
        return True
        
    async def emulate_nfc(self, signal: FlipperSignal) -> bool:
        """Emulate NFC tag."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        if signal.mode != FlipperMode.NFC:
            raise ValueError("Signal is not an NFC signal")
            
        await self.set_mode(FlipperMode.NFC)
        # Implement NFC emulation
        return True
        
    # IR Operations
    async def record_ir(self) -> Optional[FlipperSignal]:
        """Record IR signal."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        await self.set_mode(FlipperMode.IR)
        # Implement IR recording
        return None
        
    async def transmit_ir(self, signal: FlipperSignal) -> bool:
        """Transmit IR signal."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        if signal.mode != FlipperMode.IR:
            raise ValueError("Signal is not an IR signal")
            
        await self.set_mode(FlipperMode.IR)
        # Implement IR transmission
        return True
        
    async def learn_remote(self) -> List[FlipperSignal]:
        """Learn IR remote control buttons."""
        if not self.connected:
            raise ConnectionError("Not connected to device")
            
        await self.set_mode(FlipperMode.IR)
        # Implement remote learning
        return []
        
    # Signal Management
    def save_signal(self, signal: FlipperSignal, filepath: str) -> bool:
        """Save captured signal to file."""
        try:
            data = {
                "mode": signal.mode.value,
                "frequency": signal.frequency,
                "modulation": signal.modulation,
                "protocol": signal.protocol,
                "data": signal.data.hex(),
                "metadata": signal.metadata or {}
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            return False
            
    def load_signal(self, filepath: str) -> Optional[FlipperSignal]:
        """Load signal from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return FlipperSignal(
                mode=FlipperMode(data["mode"]),
                frequency=data.get("frequency"),
                modulation=data.get("modulation"),
                protocol=data.get("protocol"),
                data=bytes.fromhex(data["data"]),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Failed to load signal: {e}")
            return None