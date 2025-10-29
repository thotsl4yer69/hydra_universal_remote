"""Signal library management for Hydra Universal Remote.

Handles loading, parsing, and organizing signal files from various sources.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import json
import logging
from dataclasses import dataclass
from ..device.subghz import SubGHzSignal, ModulationType

logger = logging.getLogger(__name__)

@dataclass
class SignalMetadata:
    """Metadata for a stored signal."""
    name: str
    frequency: float
    modulation: str
    protocol: Optional[str]
    category: str
    description: Optional[str] = None
    tags: List[str] = None

class SignalLibrary:
    """Manages a collection of signals and their metadata."""
    
    def __init__(self, base_path: Path):
        """Initialize signal library.
        
        Args:
            base_path: Base directory for signal storage
        """
        self.base_path = Path(base_path)
        self.signals: Dict[str, SignalMetadata] = {}
        self._ensure_directories()
        self._load_metadata()
        
    def _ensure_directories(self):
        """Create necessary directory structure."""
        categories = ['automotive', 'garage', 'security', 'industrial', 'custom']
        for category in categories:
            (self.base_path / category).mkdir(parents=True, exist_ok=True)
            
    def load_signal_file(self, file_path: Path) -> Optional[SubGHzSignal]:
        """Load a signal file in any supported format.
        
        Args:
            file_path: Path to signal file
            
        Returns:
            Loaded signal or None if loading fails
        """
        try:
            if file_path.suffix == '.json':
                return SubGHzSignal.from_file(file_path)
            elif file_path.suffix == '.sub':
                # Parse Flipper Zero .sub file format
                with open(file_path, 'r') as f:
                    content = f.read()
                # Basic .sub file parsing
                metadata = {}
                data = b''
                for line in content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                        
                if 'Frequency' in metadata and 'Protocol' in metadata:
                    return SubGHzSignal(
                        frequency=float(metadata['Frequency']),
                        modulation=metadata.get('Modulation', 'ASK'),
                        data=data,  # Raw data would need proper parsing
                        protocol=metadata.get('Protocol')
                    )
            return None
        except Exception as e:
            logger.error(f"Failed to load signal {file_path}: {e}")
            return None
            
    def add_signal(self, 
                   signal: SubGHzSignal, 
                   name: str,
                   category: str,
                   description: str = None,
                   tags: List[str] = None) -> bool:
        """Add a signal to the library.
        
        Args:
            signal: Signal to add
            name: Signal name
            category: Signal category (automotive, garage, etc)
            description: Optional signal description
            tags: Optional tags for searching/filtering
            
        Returns:
            True if signal was added successfully
        """
        try:
            # Validate category
            category_path = self.base_path / category
            if not category_path.exists():
                category_path.mkdir(parents=True)
                
            # Create metadata
            metadata = SignalMetadata(
                name=name,
                frequency=signal.frequency,
                modulation=signal.modulation.value,
                protocol=signal.protocol,
                category=category,
                description=description,
                tags=tags or []
            )
            
            # Save signal file
            signal_path = category_path / f"{name}.json"
            if signal.to_file(signal_path):
                self.signals[name] = metadata
                self._save_metadata()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to add signal {name}: {e}")
            return False
            
    def get_signal(self, name: str) -> Optional[SubGHzSignal]:
        """Retrieve a signal by name.
        
        Args:
            name: Signal name
            
        Returns:
            Signal if found, None otherwise
        """
        if name not in self.signals:
            return None
            
        metadata = self.signals[name]
        signal_path = self.base_path / metadata.category / f"{name}.json"
        return SubGHzSignal.from_file(signal_path)
        
    def get_categories(self) -> List[str]:
        """Get list of signal categories."""
        return sorted(set(meta.category for meta in self.signals.values()))
        
    def get_signals_in_category(self, category: str) -> List[SignalMetadata]:
        """Get all signals in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of signal metadata
        """
        return [
            meta for meta in self.signals.values()
            if meta.category == category
        ]
        
    def search_signals(self, 
                      text: str = None,
                      frequency: float = None,
                      protocol: str = None,
                      tags: List[str] = None) -> List[SignalMetadata]:
        """Search signals by various criteria.
        
        Args:
            text: Text to search in name/description
            frequency: Specific frequency to match
            protocol: Specific protocol to match
            tags: Tags that must all be present
            
        Returns:
            List of matching signal metadata
        """
        results = []
        
        for meta in self.signals.values():
            # Check all criteria that were specified
            if text and text.lower() not in meta.name.lower() and (
                meta.description and text.lower() not in meta.description.lower()):
                continue
                
            if frequency and abs(meta.frequency - frequency) > 0.1:  # 0.1 MHz tolerance
                continue
                
            if protocol and meta.protocol != protocol:
                continue
                
            if tags and not all(tag in (meta.tags or []) for tag in tags):
                continue
                
            results.append(meta)
            
        return results
        
    def _save_metadata(self):
        """Save library metadata to disk."""
        metadata_path = self.base_path / "metadata.json"
        try:
            metadata = {
                name: {
                    "name": meta.name,
                    "frequency": meta.frequency,
                    "modulation": meta.modulation,
                    "protocol": meta.protocol,
                    "category": meta.category,
                    "description": meta.description,
                    "tags": meta.tags
                }
                for name, meta in self.signals.items()
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            
    def _load_metadata(self):
        """Load library metadata from disk."""
        metadata_path = self.base_path / "metadata.json"
        if not metadata_path.exists():
            return
            
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            self.signals = {
                name: SignalMetadata(**meta)
                for name, meta in metadata.items()
            }
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            
    def import_from_directory(self, directory: Path) -> int:
        """Import all signal files from a directory.
        
        Args:
            directory: Directory containing signal files
            
        Returns:
            Number of signals successfully imported
        """
        count = 0
        for file_path in Path(directory).rglob("*"):
            if file_path.suffix in ['.json', '.sub']:
                signal = self.load_signal_file(file_path)
                if signal:
                    # Use filename as signal name
                    name = file_path.stem
                    # Try to determine category from parent directory
                    category = file_path.parent.name
                    if category not in self.get_categories():
                        category = 'custom'
                        
                    if self.add_signal(signal, name, category):
                        count += 1
                        
        return count