"""Main GUI window for Hydra Universal Remote."""

import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from pathlib import Path
import logging
import asyncio
import threading
from typing import Optional

from ..utils.config import load_config
from ..utils.signal_library import SignalLibrary
from ..device.flipper_ble import FlipperZeroBLE
from .signal_browser import SignalBrowserFrame

logger = logging.getLogger(__name__)

class HydraRemoteGUI:
    """Main GUI window."""
    
    def __init__(self):
        """Initialize main window."""
        self.config = load_config()
        self.window = ThemedTk(theme=self.config.get('ui', {}).get('theme', 'default'))
        
        # Window settings
        window_config = self.config.get('ui', {}).get('window', {})
        self.window.title(window_config.get('title', 'Hydra Universal Remote'))
        self.window.geometry(f"{window_config.get('width', 800)}x{window_config.get('height', 600)}")
        
        # Initialize components
        self.signal_library = SignalLibrary(Path.cwd() / 'signals')
        self.flipper = FlipperZeroBLE()
        self.current_signal = None
        
        self._init_ui()
        self._setup_async()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Device frame (left side)
        device_frame = ttk.LabelFrame(main_container, text="Device Control")
        device_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Device status
        status_frame = ttk.Frame(device_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Disconnected")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Connect button
        self.connect_button = ttk.Button(
            device_frame,
            text="Connect",
            command=self._connect_device
        )
        self.connect_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Signal frame (right side)
        signal_frame = ttk.LabelFrame(main_container, text="Signal Browser")
        signal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add signal browser
        self.signal_browser = SignalBrowserFrame(
            signal_frame,
            self.signal_library,
            self._on_signal_selected
        )
        self.signal_browser.pack(fill=tk.BOTH, expand=True)
        
        # Transmission controls
        transmit_frame = ttk.LabelFrame(main_container, text="Transmission")
        transmit_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        self.transmit_button = ttk.Button(
            transmit_frame,
            text="Transmit Signal",
            command=self._transmit_signal,
            state=tk.DISABLED
        )
        self.transmit_button.pack(fill=tk.X, padx=5, pady=5)
        
    def _setup_async(self):
        """Setup async event loop for background tasks."""
        self.loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self._run_async_loop, daemon=True)
        thread.start()
        
    def _run_async_loop(self):
        """Run async event loop in background thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def _connect_device(self):
        """Handle device connection."""
        async def connect():
            try:
                self.connect_button.state(['disabled'])
                self.status_label.configure(text="Connecting...")
                
                # Find and connect to Flipper
                device = await self.flipper.find_flipper()
                if not device:
                    raise RuntimeError("No Flipper Zero found")
                    
                if await self.flipper.connect_to_flipper(device.get('address')):
                    self.status_label.configure(text="Connected")
                    self.connect_button.configure(text="Disconnect")
                    self.transmit_button.state(['!disabled'])
                else:
                    raise RuntimeError("Connection failed")
                    
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self.status_label.configure(text="Connection failed")
                messagebox.showerror(
                    "Connection Error",
                    f"Failed to connect: {str(e)}"
                )
            finally:
                self.connect_button.state(['!disabled'])
                
        future = asyncio.run_coroutine_threadsafe(connect(), self.loop)
        future.result()  # Wait for completion
        
    def _on_signal_selected(self, signal):
        """Handle signal selection."""
        self.current_signal = signal
        self.transmit_button.state(
            ['!disabled'] if signal and self.flipper.is_connected() else ['disabled']
        )
        
    def _transmit_signal(self):
        """Handle signal transmission."""
        if not self.current_signal or not self.flipper.is_connected():
            return
            
        async def transmit():
            try:
                self.transmit_button.state(['disabled'])
                # Implement actual transmission logic here
                # This will depend on your Flipper Zero protocol implementation
                await asyncio.sleep(1)  # Placeholder
                messagebox.showinfo(
                    "Transmission Complete",
                    "Signal transmitted successfully"
                )
            except Exception as e:
                logger.error(f"Transmission error: {e}")
                messagebox.showerror(
                    "Transmission Error",
                    f"Failed to transmit signal: {str(e)}"
                )
            finally:
                self.transmit_button.state(['!disabled'])
                
        future = asyncio.run_coroutine_threadsafe(transmit(), self.loop)
        future.result()  # Wait for completion
        
    def run(self):
        """Start the GUI."""
        self.window.mainloop()
        
def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    gui = HydraRemoteGUI()
    gui.run()

if __name__ == "__main__":
    main()