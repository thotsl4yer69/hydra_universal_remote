"""
Sub-GHz protocol handling and signal analysis for Flipper Zero.
Based on official protocol specifications and community research.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging
import struct
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ModulationType(Enum):
    """Supported modulation types."""
    AM = "AM"  # Amplitude Modulation
    FM = "FM"  # Frequency Modulation
    ASK = "ASK"  # Amplitude Shift Keying
    FSK = "FSK"  # Frequency Shift Keying
    OOK = "OOK"  # On-Off Keying
    PSK = "PSK"  # Phase Shift Keying

class DecodingType(Enum):
    """Signal decoding methods."""
    MANCHESTER = "manchester"
    DIFFERENTIAL = "differential"
    BINARY = "binary"
    PWM = "pwm"
    RAW = "raw"

@dataclass
class SubGHzProtocolInfo:
    """Protocol definition and parameters."""
    name: str
    frequencies: List[float]
    modulation: ModulationType
    bit_rate: float
    deviation: Optional[float] = None  # For FSK
    preamble: Optional[bytes] = None
    decode_type: DecodingType = DecodingType.BINARY
    min_repeats: int = 1
    gap_limit: Optional[int] = None
    
class SubGHzProtocolRegistry:
    """Registry of known Sub-GHz protocols."""
    
    # Common protocols and their parameters
    PROTOCOLS = {
        "princeton": SubGHzProtocolInfo(
            name="Princeton",
            frequencies=[433.92],
            modulation=ModulationType.ASK,
            bit_rate=2000,
            decode_type=DecodingType.MANCHESTER,
            min_repeats=2
        ),
        "keeloq": SubGHzProtocolInfo(
            name="KeeLoq",
            frequencies=[433.92, 434.42, 868.35],
            modulation=ModulationType.FSK,
            bit_rate=1500,
            deviation=50000,
            decode_type=DecodingType.MANCHESTER,
            min_repeats=2
        ),
        "nice_flor_s": SubGHzProtocolInfo(
            name="Nice FLO",
            frequencies=[433.92],
            modulation=ModulationType.AM,
            bit_rate=1000,
            decode_type=DecodingType.MANCHESTER,
            min_repeats=3
        ),
        "chamberlain": SubGHzProtocolInfo(
            name="Chamberlain",
            frequencies=[300.0, 390.0],
            modulation=ModulationType.OOK,
            bit_rate=2000,
            decode_type=DecodingType.BINARY,
            min_repeats=2,
            gap_limit=15000
        ),
        # Add more protocols as needed
    }
    
    @classmethod
    def get_protocol(cls, name: str) -> Optional[SubGHzProtocolInfo]:
        """Get protocol by name."""
        return cls.PROTOCOLS.get(name.lower())
        
    @classmethod
    def get_protocols_for_frequency(cls, freq: float, 
                                  tolerance: float = 0.1) -> List[SubGHzProtocolInfo]:
        """Get protocols that operate on given frequency."""
        matching = []
        for protocol in cls.PROTOCOLS.values():
            for protocol_freq in protocol.frequencies:
                if abs(protocol_freq - freq) <= tolerance:
                    matching.append(protocol)
                    break
        return matching

class SignalAnalyzer:
    """Sub-GHz signal analysis tools."""
    
    @staticmethod
    def detect_modulation(samples: np.ndarray) -> ModulationType:
        """Detect modulation type from raw samples."""
        # Calculate signal properties
        amplitude_var = np.var(np.abs(samples))
        frequency_var = np.var(np.angle(samples[1:] * np.conj(samples[:-1])))
        phase_var = np.var(np.angle(samples))
        
        # Simple heuristic classification
        if amplitude_var > 0.5:  # High amplitude variation
            return ModulationType.AM if amplitude_var > 0.8 else ModulationType.ASK
        elif frequency_var > 0.5:  # High frequency variation
            return ModulationType.FM if frequency_var > 0.8 else ModulationType.FSK
        elif phase_var > 0.5:  # High phase variation
            return ModulationType.PSK
        else:
            return ModulationType.OOK
            
    @staticmethod
    def extract_pulses(samples: np.ndarray, threshold: float = 0.5) -> List[int]:
        """Extract pulse lengths from raw samples."""
        # Convert to amplitude
        amplitude = np.abs(samples)
        
        # Threshold to binary signal
        binary = amplitude > threshold
        
        # Find transitions
        transitions = np.diff(binary.astype(int))
        transition_points = np.where(transitions != 0)[0]
        
        # Calculate pulse lengths
        if len(transition_points) < 2:
            return []
            
        pulses = []
        for i in range(len(transition_points) - 1):
            pulse_length = transition_points[i + 1] - transition_points[i]
            pulses.append(pulse_length)
            
        return pulses
        
    @staticmethod
    def detect_bit_rate(pulses: List[int]) -> float:
        """Estimate bit rate from pulse lengths."""
        if not pulses:
            return 0.0
            
        # Find most common pulse length (mode)
        pulse_counts = {}
        for pulse in pulses:
            pulse_counts[pulse] = pulse_counts.get(pulse, 0) + 1
            
        base_length = max(pulse_counts.items(), key=lambda x: x[1])[0]
        return 1000000 / base_length  # Convert to bits per second
        
    @staticmethod
    def decode_manchester(pulses: List[int], tolerance: float = 0.2) -> Optional[bytes]:
        """Decode Manchester encoded data."""
        if not pulses or len(pulses) < 2:
            return None
            
        # Estimate base clock period
        clock = min(pulses)
        bits = []
        
        i = 0
        while i < len(pulses) - 1:
            p1, p2 = pulses[i], pulses[i + 1]
            
            # Check if pulse pair matches Manchester pattern
            if abs(p1 - clock) <= tolerance * clock and abs(p2 - clock) <= tolerance * clock:
                if p1 > p2:
                    bits.append(1)  # Rising edge
                else:
                    bits.append(0)  # Falling edge
                i += 2
            else:
                # Invalid Manchester code
                return None
                
        # Convert bits to bytes
        if not bits:
            return None
            
        result = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | bits[i + j]
                result.append(byte)
                
        return bytes(result)

class SubGHzSignal:
    """Container for captured Sub-GHz signals."""
    
    def __init__(self, frequency: float, modulation: ModulationType):
        """Initialize signal container."""
        self.frequency = frequency
        self.modulation = modulation
        self.raw_samples = np.array([], dtype=np.complex64)
        self.pulses = []
        self.decoded_data: Optional[bytes] = None
        self.protocol: Optional[str] = None
        self.metadata: Dict = {}
        
    def add_samples(self, samples: np.ndarray):
        """Add raw samples to signal."""
        self.raw_samples = np.concatenate([self.raw_samples, samples])
        
    def analyze(self):
        """Analyze signal and attempt protocol detection."""
        if len(self.raw_samples) == 0:
            return
            
        # Extract pulses
        self.pulses = SignalAnalyzer.extract_pulses(self.raw_samples)
        if not self.pulses:
            return
            
        # Estimate bit rate
        bit_rate = SignalAnalyzer.detect_bit_rate(self.pulses)
        self.metadata['bit_rate'] = bit_rate
        
        # Try to identify protocol
        potential_protocols = SubGHzProtocolRegistry.get_protocols_for_frequency(
            self.frequency
        )
        
        for protocol_info in potential_protocols:
            if protocol_info.modulation == self.modulation:
                # Try decoding
                if protocol_info.decode_type == DecodingType.MANCHESTER:
                    data = SignalAnalyzer.decode_manchester(self.pulses)
                    if data:
                        self.decoded_data = data
                        self.protocol = protocol_info.name
                        return
                        
    def to_file(self, path: Path) -> bool:
        """Save signal to file."""
        try:
            data = {
                "frequency": self.frequency,
                "modulation": self.modulation.value,
                "protocol": self.protocol,
                "metadata": self.metadata,
                "raw_samples": self.raw_samples.tobytes().hex(),
                "decoded_data": self.decoded_data.hex() if self.decoded_data else None
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            return False
            
    @classmethod
    def from_file(cls, path: Path) -> Optional['SubGHzSignal']:
        """Load signal from file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            signal = cls(
                frequency=data["frequency"],
                modulation=ModulationType(data["modulation"])
            )
            
            signal.raw_samples = np.frombuffer(
                bytes.fromhex(data["raw_samples"]),
                dtype=np.complex64
            )
            
            if data["decoded_data"]:
                signal.decoded_data = bytes.fromhex(data["decoded_data"])
                
            signal.protocol = data["protocol"]
            signal.metadata = data["metadata"]
            
            return signal
        except Exception as e:
            logger.error(f"Failed to load signal: {e}")
            return None

"""
Sub-GHz protocol logic for Flipper Zero integration.
"""

class SubGhzSignal:
    def __init__(self, frequency: float, modulation: str, data: bytes, protocol: Optional[str] = None):
        self.frequency = frequency
        self.modulation = modulation
        self.data = data
        self.protocol = protocol

class SubGhzManager:
    """Handles Sub-GHz signal scan, analysis, and replay."""
    def __init__(self, flipper_device):
        self.device = flipper_device

    async def scan_signal(self, timeout: int = 5) -> Optional[SubGhzSignal]:
        """
        Scan/record Sub-GHz signal from Flipper Zero.
        Returns SubGhzSignal or None.
        """
        # Example: send protobuf scan request, receive signal
        try:
            # Replace with actual protobuf message per flipperzero-protobuf-py
            request = b"subghz_scan_request"
            await self.device.send_command(request)
            response = await self.device.read_response()
            # Parse response (replace with actual parsing)
            if response:
                # Dummy parse: frequency, modulation, data
                frequency = 433.92
                modulation = "ASK"
                data = response
                return SubGhzSignal(frequency, modulation, data)
            return None
        except Exception as e:
            logger.error(f"Sub-GHz scan failed: {e}")
            return None

    async def analyze_signal(self, signal: SubGhzSignal) -> Dict[str, Any]:
        """
        Analyze signal for protocol/modulation/frequency.
        Returns dict with analysis results.
        """
        # Placeholder: implement real analysis or call Flipper's built-in
        return {
            "frequency": signal.frequency,
            "modulation": signal.modulation,
            "protocol": signal.protocol or "Unknown",
            "data_len": len(signal.data)
        }

    async def replay_signal(self, signal: SubGhzSignal) -> bool:
        """
        Replay Sub-GHz signal via Flipper Zero.
        """
        try:
            # Replace with actual protobuf replay message
            replay_msg = b"subghz_replay:" + signal.data
            await self.device.send_command(replay_msg)
            ack = await self.device.read_response()
            return bool(ack)
        except Exception as e:
            logger.error(f"Sub-GHz replay failed: {e}")
            return False