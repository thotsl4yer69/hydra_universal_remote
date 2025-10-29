"""Hydra Universal Remote main application module."""

import asyncio
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import queue
import functools

from .utils.config import load_config
from .device.ble_adapter import BLEAdapter

class HydraRemoteGUI:
    def __init__(self):
        """Initialize the GUI window and components."""
        self.config = load_config()
        self.window = ThemedTk(theme=self.config.get("ui", {}).get("theme", "default"))
        
        # Configure window
        window_config = self.config.get("ui", {}).get("window", {})
        self.window.title(window_config.get("title", "Hydra Universal Remote"))
        self.window.geometry(f"{window_config.get('width', 800)}x{window_config.get('height', 600)}")
        
        # Initialize BLE
        self.ble = BLEAdapter()
        
        # Create UI components
        self._create_widgets()
        
        # BLE state
        self.scanning = False
        self.devices = []
        
        # Setup async event loop
        self.loop = asyncio.new_event_loop()
        self.queue = queue.Queue()
        self.thread = None
    
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
        self.device_list.bind('<<ListboxSelect>>', self._on_device_select)
        self.selected_device_index = None
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, pady=5)

        # Connect button
        self.connect_button = ttk.Button(
            self.main_frame,
            text="Connect",
            command=self._connect_selected_device,
            state="disabled"
        )
        self.connect_button.grid(row=3, column=0, pady=5)

        # Disconnect button
        self.disconnect_button = ttk.Button(
            self.main_frame,
            text="Disconnect",
            command=self._disconnect_device,
            state="disabled"
        )
        self.disconnect_button.grid(row=4, column=0, pady=5)
    
    def _create_async_thread(self):
        """Create and start the async event loop thread."""
        if self.thread is not None:
            return
            
        def run_async_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
            
        self.thread = threading.Thread(target=run_async_loop, daemon=True)
        self.thread.start()
        
    def _queue_async_task(self, coro):
        """Queue an async task and handle its result in the main thread."""
        if self.thread is None:
            self._create_async_thread()
            
        async def handle_task():
            try:
                result = await coro
                self.queue.put(("success", result))
            except Exception as e:
                self.queue.put(("error", str(e)))
                
        asyncio.run_coroutine_threadsafe(handle_task(), self.loop)
    
    def _process_queue(self):
        """Process async results from the queue."""
        try:
            while True:
                status, result = self.queue.get_nowait()
                if status == "success" and isinstance(result, list):
                    # Update device list with scan results
                    self.device_list.delete(0, tk.END)
                    for device in result:
                        name = device["name"] or "Unknown Device"
                        addr = device["address"]
                        self.device_list.insert(tk.END, f"{name} ({addr})")
                    self.devices = result
                    self.selected_device_index = None
                    self.connect_button.config(state="disabled")
                    self.status_label.config(text=f"Found {len(result)} devices")
                elif status == "error":
                    self.status_label.config(text=f"Error: {result}")
                    
                self.scanning = False
                self.scan_button.config(state="normal")
        except queue.Empty:
            pass
            
        # Schedule next queue check
        if not self.window.winfo_exists():
            return
        self.window.after(100, self._process_queue)
    
    def _start_scan(self):
        """Start BLE device scan."""
        if self.scanning:
            return
            
        self.scanning = True
        self.scan_button.config(state="disabled")
        self.status_label.config(text="Scanning...")
        self.device_list.delete(0, tk.END)
        self.connect_button.config(state="disabled")
        self.disconnect_button.config(state="disabled")
        
        # Queue the scan operation
        timeout = self.config.get("ble", {}).get("scan_timeout", 5.0)
        self._queue_async_task(self.ble.scan(timeout=timeout))

    def _on_device_select(self, event):
        selection = self.device_list.curselection()
        if selection:
            self.selected_device_index = selection[0]
            self.connect_button.config(state="normal")
        else:
            self.selected_device_index = None
            self.connect_button.config(state="disabled")

    def _connect_selected_device(self):
        if self.selected_device_index is None or not self.devices:
            return
        device = self.devices[self.selected_device_index]
        address = device["address"]
        self.status_label.config(text=f"Connecting to {address}...")
        self.connect_button.config(state="disabled")
        self.scan_button.config(state="disabled")
        self._queue_async_task(self._async_connect(address))

    async def _async_connect(self, address):
        try:
            connected = await self.ble.connect(address)
            if connected:
                self.status_label.config(text=f"Connected to {address}")
                self.disconnect_button.config(state="normal")
                self.connect_button.config(state="disabled")
                self.scan_button.config(state="disabled")
            else:
                self.status_label.config(text=f"Failed to connect to {address}")
                self.disconnect_button.config(state="disabled")
                self.connect_button.config(state="normal")
                self.scan_button.config(state="normal")
        except Exception as e:
            self.status_label.config(text=f"Connect error: {str(e)}")
            self.disconnect_button.config(state="disabled")
            self.connect_button.config(state="normal")
            self.scan_button.config(state="normal")

    def _disconnect_device(self):
        self.status_label.config(text="Disconnecting...")
        self.disconnect_button.config(state="disabled")
        self._queue_async_task(self._async_disconnect())

    async def _async_disconnect(self):
        try:
            await self.ble.disconnect()
            self.status_label.config(text="Disconnected")
            self.connect_button.config(state="disabled")
            self.scan_button.config(state="normal")
        except Exception as e:
            self.status_label.config(text=f"Disconnect error: {str(e)}")
            self.scan_button.config(state="normal")
    
    def run(self):
        """Start the GUI event loop."""
        # Start queue processing
        self._process_queue()
        # Run the main loop
        self.window.mainloop()
        # Cleanup
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

def main():
    """Application entry point."""
    app = HydraRemoteGUI()
    app.run()

if __name__ == "__main__":
    main()
