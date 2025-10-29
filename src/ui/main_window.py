"""Main GUI window for Hydra Universal Remote."""

import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from pathlib import Path
import logging

from ..core.logging_utils import configure_logging
from ..core.runtime import runtime
from ..utils.config import load_config
from ..utils.signal_library import SignalLibrary
from ..device.device_manager import DeviceManager
from .device_frame import DeviceConnectionFrame
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
        self.device_manager = DeviceManager()
        self.current_signal = None
        self._runtime = runtime
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main container
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Device frame (left side)
        self.device_frame = DeviceConnectionFrame(
            main_container,
            self.device_manager,
            self._on_connection_changed
        )
        self.device_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
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
        
    def _on_connection_changed(self, is_connected: bool):
        """Handle connection state changes.
        
        Args:
            is_connected: True if device is connected, False otherwise
        """
        # Enable/disable transmit button based on connection state
        # and whether a signal is selected
        if is_connected and self.current_signal:
            self.transmit_button.state(['!disabled'])
        else:
            self.transmit_button.state(['disabled'])
            
    def _on_signal_selected(self, signal):
        """Handle signal selection."""
        self.current_signal = signal
        self.transmit_button.state(
            ['!disabled'] if signal and self.device_manager.is_connected() else ['disabled']
        )
        
    def _transmit_signal(self):
        """Handle signal transmission."""
        if not self.current_signal or not self.device_manager.is_connected():
            return
            
        self.transmit_button.state(['disabled'])

        async def transmit():
            return await self.device_manager.transmit_signal(self.current_signal)

        future = self._runtime.run_in_background(transmit())

        def _on_complete(_future):
            try:
                success = _future.result()
            except Exception as exc:
                logger.error("Transmission error: %s", exc)
                messagebox.showerror("Transmission Error", f"Failed to transmit signal: {exc}")
            else:
                if success:
                    messagebox.showinfo("Success", "Signal transmitted successfully")
                else:
                    messagebox.showerror("Transmission Error", "Failed to transmit signal")
            finally:
                if self.device_manager.is_connected():
                    self.transmit_button.state(['!disabled'])

        future.add_done_callback(lambda fut: self.window.after(0, _on_complete, fut))
        
    def run(self):
        """Start the GUI."""
        self.window.mainloop()
        
    def cleanup(self):
        """Clean up resources."""
        if self.device_manager.is_connected():
            future = self._runtime.run_in_background(self.device_manager.disconnect())

            def _wait(_future):
                try:
                    _future.result()
                except Exception as exc:
                    logger.warning("Device disconnect failed: %s", exc)

            future.add_done_callback(lambda fut: self.window.after(0, _wait, fut))

        self._runtime.shutdown()
        
def main():
    """Main entry point."""
    configure_logging()
    gui = HydraRemoteGUI()
    try:
        gui.run()
    finally:
        gui.cleanup()

if __name__ == "__main__":
    main()