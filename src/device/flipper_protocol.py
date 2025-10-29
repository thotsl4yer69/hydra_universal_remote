"""
Flipper Zero protocol implementation.
Handles low-level communication and message formatting.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union, List
import json
import struct
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

class FlipperProtocolError(Exception):
    """Base exception for protocol errors."""
    pass

class MessageType(Enum):
    """RPC message types."""
    COMMAND = 0
    RESPONSE = 1
    EVENT = 2
    ERROR = 3

@dataclass
class RPCMessage:
    """RPC message container."""
    type: MessageType
    command_id: int
    command: str
    args: Dict[str, Any]
    data: Optional[bytes] = None

class FlipperProtocol:
    """
    Implementation of Flipper Zero's RPC protocol.
    Based on official documentation and community implementations.
    """
    
    def __init__(self):
        """Initialize protocol handler."""
        self.command_id = 0
        self._callbacks = {}
        self._responses = {}
        self._events = asyncio.Queue()
        
    def _get_next_command_id(self) -> int:
        """Get next command ID."""
        self.command_id = (self.command_id + 1) % 0xFFFFFFFF
        return self.command_id
        
    def encode_message(self, msg: RPCMessage) -> bytes:
        """Encode message to wire format."""
        # Format: [Type][CommandID][CommandLen][Command][ArgsLen][Args][DataLen][Data]
        command_bytes = msg.command.encode('utf-8')
        args_bytes = json.dumps(msg.args).encode('utf-8')
        data_bytes = msg.data or b''
        
        header = struct.pack(
            '>BIIII',
            msg.type.value,
            msg.command_id,
            len(command_bytes),
            len(args_bytes),
            len(data_bytes)
        )
        
        return header + command_bytes + args_bytes + data_bytes
        
    def decode_message(self, data: bytes) -> RPCMessage:
        """Decode message from wire format."""
        try:
            # Parse header
            header_size = struct.calcsize('>BIIII')
            if len(data) < header_size:
                raise FlipperProtocolError("Message too short")
                
            msg_type, cmd_id, cmd_len, args_len, data_len = struct.unpack(
                '>BIIII', data[:header_size]
            )
            
            # Parse sections
            offset = header_size
            command = data[offset:offset + cmd_len].decode('utf-8')
            offset += cmd_len
            
            args_data = data[offset:offset + args_len].decode('utf-8')
            args = json.loads(args_data) if args_data else {}
            offset += args_len
            
            msg_data = data[offset:offset + data_len] if data_len > 0 else None
            
            return RPCMessage(
                type=MessageType(msg_type),
                command_id=cmd_id,
                command=command,
                args=args,
                data=msg_data
            )
            
        except (struct.error, json.JSONDecodeError, ValueError) as e:
            raise FlipperProtocolError(f"Failed to decode message: {e}")
            
    async def send_command(self, transport: asyncio.Transport, command: str,
                          args: Dict[str, Any] = None, data: bytes = None,
                          timeout: float = 5.0) -> RPCMessage:
        """
        Send command and wait for response.
        
        Args:
            transport: Transport to send message over
            command: Command string
            args: Optional command arguments
            data: Optional binary data
            timeout: Response timeout in seconds
            
        Returns:
            Response message
            
        Raises:
            FlipperProtocolError: On protocol errors
            asyncio.TimeoutError: On response timeout
        """
        cmd_id = self._get_next_command_id()
        message = RPCMessage(
            type=MessageType.COMMAND,
            command_id=cmd_id,
            command=command,
            args=args or {},
            data=data
        )
        
        # Create future for response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._responses[cmd_id] = future
        
        try:
            # Send message
            encoded = self.encode_message(message)
            transport.write(encoded)
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout)
            
            if response.type == MessageType.ERROR:
                raise FlipperProtocolError(
                    f"Command failed: {response.args.get('error', 'Unknown error')}"
                )
                
            return response
            
        finally:
            self._responses.pop(cmd_id, None)
            
    def handle_response(self, message: RPCMessage):
        """Handle response message."""
        if message.command_id in self._responses:
            future = self._responses[message.command_id]
            if not future.done():
                future.set_result(message)
                
    def handle_event(self, message: RPCMessage):
        """Handle event message."""
        self._events.put_nowait(message)
        
    async def get_next_event(self) -> RPCMessage:
        """Get next event from queue."""
        return await self._events.get()
        
    def register_callback(self, event_type: str, callback):
        """Register callback for event type."""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
        
    def unregister_callback(self, event_type: str, callback):
        """Unregister callback for event type."""
        if event_type in self._callbacks:
            self._callbacks[event_type] = [
                cb for cb in self._callbacks[event_type]
                if cb != callback
            ]