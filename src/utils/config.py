"""Common utility functions for configuration, validation and type checking."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def load_yaml(path: str) -> Dict[str, Any]:
    """Load and parse a YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Dict containing parsed YAML content
        
    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If YAML parsing fails
    """
    with open(path) as f:
        return yaml.safe_load(f)

def get_config_path() -> str:
    """Get the absolute path to config.yaml.
    
    Looks in src/config/config.yaml relative to this file.
    
    Returns:
        Absolute path to config file
    """
    return str(Path(__file__).resolve().parents[1] / "config" / "config.yaml")

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load application configuration from YAML.
    
    Args:
        path: Optional path to config file. If not provided, uses default location.
        
    Returns:
        Dict containing configuration. Returns empty dict if file not found or invalid.
    """
    try:
        config_path = path or get_config_path()
        return load_yaml(config_path)
    except (FileNotFoundError, yaml.YAMLError):
        return {}