"""
Flipper Zero configuration and constants.
Based on official Flipper Zero protocols and community guidelines.
"""

from enum import Enum
from typing import Dict, Any

# USB Protocol Constants
FLIPPER_USB_MODES = {
    "CDC": (0x0483, 0x5740),  # Standard CDC mode
    "DFU": (0x0483, 0xdf11),  # DFU mode
    "CLI": (0x0483, 0x5741),  # CLI mode
    "SERIAL": (0x0483, 0x5742)  # Serial mode
}

# Serial Communication
SERIAL_CONFIG = {
    "baudrate": 115200,
    "timeout": 1.0,
    "write_timeout": 1.0,
    "bytesize": 8,
    "parity": 'N',
    "stopbits": 1
}

# Sub-GHz Configuration
class SubGHzPreset(Enum):
    """Standard Sub-GHz frequency presets."""
    PRESET_FP = "FuriHalSubGhzPresetFP"  # Fine Power
    PRESET_OOK_650KHZ = "FuriHalSubGhzPresetOok650Khz"
    PRESET_OOK_270KHZ = "FuriHalSubGhzPresetOok270Khz"
    PRESET_2FSK_GAP_2400 = "FuriHalSubGhzPreset2FSKDev238Khz"

# Common frequencies in MHz
COMMON_FREQUENCIES = {
    "315": 315.0,
    "433": 433.92,
    "868": 868.35,
    "915": 915.0
}

# Frequency ranges (MHz)
FREQUENCY_RANGES = {
    "US": {
        "min": 299.999755,
        "max": 348.000061,
        "alt_min": 387.252014,
        "alt_max": 464.000000
    },
    "EU": {
        "min": 299.999755,
        "max": 348.000061,
        "alt_min": 387.252014,
        "alt_max": 464.000000
    }
}

# Protocol definitions
SUPPORTED_PROTOCOLS = {
    "SUB_GHZ": [
        "Princeton", "CAME", "Nice FLO", "FAAC SLH", "Gate TX", "DoorHan",
        "Marantec", "BETT", "Linear", "Chamberlain", "Sommer", "CAM/CAME",
        "Keeloq", "Star Line", "Centurion"
    ],
    "RFID": [
        "EM4100", "HIDProx", "Indala26", "IoProx", "EM-Marin", "H10301",
        "PAC/Stanley", "Casi-Rusco"
    ],
    "NFC": [
        "ISO14443A", "ISO14443B", "ISO15693", "NTAG203", "NTAG213",
        "NTAG215", "NTAG216", "Mifare Classic", "Mifare DESFire"
    ],
    "IR": [
        "NEC", "Samsung", "LG", "Sony", "RC5", "RC6", "JVC", "Panasonic",
        "SIRC", "Samsung32"
    ]
}

# RPC Commands
RPC_COMMANDS = {
    "system": {
        "ping": "system.ping",
        "info": "system.info",
        "device_info": "system.device_info",
        "power_info": "system.power_info"
    },
    "storage": {
        "list": "storage.list",
        "read": "storage.read",
        "write": "storage.write",
        "remove": "storage.remove",
        "mkdir": "storage.mkdir"
    },
    "app": {
        "start": "app.start",
        "lock": "app.lock",
        "unlock": "app.unlock",
        "exit": "app.exit"
    }
}

# IR Remote Control Types
IR_REMOTE_TYPES = {
    "TV": ["Samsung", "LG", "Sony", "Philips", "Panasonic", "Sharp"],
    "Audio": ["Pioneer", "Denon", "Yamaha", "Onkyo", "Marantz"],
    "AC": ["Daikin", "Mitsubishi", "Toshiba", "Carrier", "LG"],
    "Projector": ["Epson", "BenQ", "Optoma", "ViewSonic"]
}

# Default save paths
DEFAULT_PATHS = {
    "subghz": "/ext/subghz",
    "rfid": "/ext/lfrfid",
    "nfc": "/ext/nfc",
    "ir": "/ext/infrared",
    "ibutton": "/ext/ibutton",
    "apps": "/ext/apps"
}

# Signal capture settings
CAPTURE_SETTINGS = {
    "subghz": {
        "sample_rate": 2000000,
        "batch_size": 1024,
        "threshold": 0.5
    },
    "rfid": {
        "sample_rate": 125000,
        "manchester": True
    },
    "ir": {
        "frequency": 38000,  # 38kHz carrier
        "duty_cycle": 0.33   # 33% duty cycle
    }
}

def get_region_frequencies(region: str = "US") -> Dict[str, float]:
    """Get allowed frequencies for a specific region."""
    if region not in FREQUENCY_RANGES:
        raise ValueError(f"Unknown region: {region}")
    return FREQUENCY_RANGES[region]

def get_protocol_list(protocol_type: str) -> list:
    """Get list of supported protocols for a given type."""
    return SUPPORTED_PROTOCOLS.get(protocol_type.upper(), [])