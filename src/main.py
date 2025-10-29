"""Hydra Universal Remote main application module."""

import asyncio
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from pathlib import Path
from typing import Dict, Any, Optional

from .utils.config import load_config
from .utils.ble import scan_for_devices, connect_device, list_services

class HydraRemoteGUI:
    def __init__(self):
        """Initialize the GUI window and components."""
        self.config = load_config()
        self.window = ThemedTk(theme=self.config.get("ui", {}).get("theme", "default"))
        
        # Configure window
        window_config = self.config.get("ui", {}).get("window", {})
        self.window.title(window_config.get("title", "Hydra Universal Remote"))
        self.window.geometry(f"{window_config.get('width', 800)}x{window_config.get('height', 600)}")
        
        # Create UI components
        self._create_widgets()
        
        # BLE state
        self.scanning = False
        self.devices = []
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scan button
        self.scan_button = ttk.Button(
            self.main_frame, 
            text="Scan for Devices",
            command=self._start_scan
        )
        self.scan_button.grid(row=0, column=0, pady=5)
        
        # Device list
        self.device_list = tk.Listbox(self.main_frame, height=10)
        self.device_list.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, pady=5)
    
    def _start_scan(self):
        """Start BLE device scan."""
        if self.scanning:
            return
            
        self.scanning = True
        self.scan_button.config(state="disabled")
        self.status_label.config(text="Scanning...")
        self.device_list.delete(0, tk.END)
        
        # Run scan in background
        asyncio.create_task(self._scan_devices())
    
    async def _scan_devices(self):
        """Perform BLE scan and update UI with results."""
        try:
            timeout = self.config.get("ble", {}).get("scan_timeout", 5.0)
            self.devices = await scan_for_devices(timeout=timeout)
            
            # Update device list
            for device in self.devices:
                name = device["name"] or "Unknown Device"
                addr = device["address"]
                self.device_list.insert(tk.END, f"{name} ({addr})")
                
            self.status_label.config(text=f"Found {len(self.devices)} devices")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            
        finally:
            self.scanning = False
            self.scan_button.config(state="normal")
    
    def run(self):
        """Start the GUI event loop."""
        self.window.mainloop()

async def run_smoke():
    """Run a smoke test to verify basic functionality."""
    print("hydra_universal_remote smoke-run")
    cfg = load_config()
    if isinstance(cfg, dict):
        print(f"loaded config keys: {list(cfg.keys())}")
    else:
        print("loaded config (non-dict)")
        
    try:
        import bleak
        print("bleak available")
    except ImportError:
        print("bleak not available")
        
    try:
        import flipperzero
        print("flipperzero protobuf available")
    except ImportError:
        print("flipperzero protobuf not available")
        
    print("smoke-run complete — no hardware accessed")

def main():
    """Application entry point."""
    app = HydraRemoteGUI()
    app.run()

if __name__ == "__main__":
    main()
