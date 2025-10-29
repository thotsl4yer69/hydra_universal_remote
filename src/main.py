"""Hydra Universal Remote main application module."""

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import queue
import functools
import logging

from .utils.config import load_config
from .device.ble_adapter import BLEAdapter
from .device.flipper_zero import FlipperZeroDevice, FlipperMode, FlipperSignal

class HydraRemoteGUI:
    def __init__(self):
        """Initialize the GUI window and components."""
        self.config = load_config()
        self.window = ThemedTk(theme=self.config.get("ui", {}).get("theme", "arc"))
        
        # Configure window
        window_config = self.config.get("ui", {}).get("window", {})
        self.window.title(window_config.get("title", "Hydra Universal Remote"))
        self.window.geometry(f"{window_config.get('width', 1000)}x{window_config.get('height', 800)}")
        
        # Initialize device interfaces
        self.ble = BLEAdapter()
        self.flipper = FlipperZeroDevice()
        
        # Create UI components
        self._create_widgets()
        
        # Device state
        self.scanning = False
        self.devices = []
        self.current_mode = None
        self.current_signal = None
        
        # Setup async event loop
        self.loop = asyncio.new_event_loop()
        self.queue = queue.Queue()
        self.thread = None
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Configure main window grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Main frame
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.columnconfigure(1, weight=1)  # Make content area expand
        
        # Left sidebar frame
        self.sidebar = ttk.Frame(self.main_frame, padding="5")
        self.sidebar.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection group in sidebar
        connection_group = ttk.LabelFrame(self.sidebar, text="Connection", padding="5")
        connection_group.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Scan button
        self.scan_button = ttk.Button(
            connection_group, 
            text="Scan for Devices",
            command=self._start_scan
        )
        self.scan_button.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Device list
        self.device_list = tk.Listbox(connection_group, height=8)
        self.device_list.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        self.device_list.bind('<<ListboxSelect>>', self._on_device_select)
        self.selected_device_index = None
        
        # Status label
        self.status_label = ttk.Label(connection_group, text="Ready")
        self.status_label.grid(row=2, column=0, pady=5)

        # Connect/Disconnect buttons
        button_frame = ttk.Frame(connection_group)
        button_frame.grid(row=3, column=0, pady=5)
        
        self.connect_button = ttk.Button(
            button_frame,
            text="Connect",
            command=self._connect_selected_device,
            state="disabled"
        )
        self.connect_button.grid(row=0, column=0, padx=2)

        self.disconnect_button = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self._disconnect_device,
            state="disabled"
        )
        self.disconnect_button.grid(row=0, column=1, padx=2)
        
        # Create notebook for different modes
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Create mode-specific frames
        self._create_subghz_frame()
        self._create_rfid_frame()
        self._create_nfc_frame()
        self._create_ir_frame()
        
        # Activity log frame at bottom
        log_frame = ttk.LabelFrame(self.main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Add log text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = scrollbar.set
        
    def _create_subghz_frame(self):
        """Create Sub-GHz mode interface."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Sub-GHz")
        
        # Frequency selection
        freq_frame = ttk.LabelFrame(frame, text="Frequency", padding="5")
        freq_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.freq_var = tk.StringVar(master=self.window, value="433.92")
        freq_entry = ttk.Entry(freq_frame, textvariable=self.freq_var, width=10)
        freq_entry.grid(row=0, column=0, padx=5)
        ttk.Label(freq_frame, text="MHz").grid(row=0, column=1)
        
        # Modulation selection
        mod_frame = ttk.LabelFrame(frame, text="Modulation", padding="5")
        mod_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.mod_var = tk.StringVar(master=self.window, value="AM")
        ttk.Radiobutton(mod_frame, text="AM", variable=self.mod_var, value="AM").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mod_frame, text="FM", variable=self.mod_var, value="FM").grid(row=0, column=1, padx=5)
        
        # Control buttons
        ctrl_frame = ttk.LabelFrame(frame, text="Controls", padding="5")
        ctrl_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(ctrl_frame, text="Start Recording", command=self._start_subghz_record).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Stop Recording", command=self._stop_subghz_record).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Transmit", command=self._transmit_subghz).grid(row=0, column=2, padx=5, pady=5)
        
    def _create_rfid_frame(self):
        """Create RFID mode interface."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="RFID")
        
        # Control buttons
        ctrl_frame = ttk.LabelFrame(frame, text="Controls", padding="5")
        ctrl_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(ctrl_frame, text="Read Card", command=self._read_rfid).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Write Card", command=self._write_rfid).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Emulate", command=self._emulate_rfid).grid(row=0, column=2, padx=5, pady=5)
        
        # Data display
        data_frame = ttk.LabelFrame(frame, text="Card Data", padding="5")
        data_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.rfid_data = tk.Text(data_frame, height=10, width=40)
        self.rfid_data.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
    def _create_nfc_frame(self):
        """Create NFC mode interface."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="NFC")
        
        # Control buttons
        ctrl_frame = ttk.LabelFrame(frame, text="Controls", padding="5")
        ctrl_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(ctrl_frame, text="Read Tag", command=self._read_nfc).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Write Tag", command=self._write_nfc).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Emulate", command=self._emulate_nfc).grid(row=0, column=2, padx=5, pady=5)
        
        # Data display
        data_frame = ttk.LabelFrame(frame, text="Tag Data", padding="5")
        data_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.nfc_data = tk.Text(data_frame, height=10, width=40)
        self.nfc_data.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
    def _create_ir_frame(self):
        """Create IR mode interface."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Infrared")
        
        # Control buttons
        ctrl_frame = ttk.LabelFrame(frame, text="Controls", padding="5")
        ctrl_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(ctrl_frame, text="Record", command=self._record_ir).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Transmit", command=self._transmit_ir).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="Learn Remote", command=self._learn_remote).grid(row=0, column=2, padx=5, pady=5)
        
        # Remote buttons display
        remote_frame = ttk.LabelFrame(frame, text="Remote Buttons", padding="5")
        remote_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.remote_buttons = tk.Text(remote_frame, height=10, width=40)
        self.remote_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
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
            await self.flipper.disconnect()
            self.status_label.config(text="Disconnected")
            self.connect_button.config(state="disabled")
            self.scan_button.config(state="normal")
        except Exception as e:
            self.status_label.config(text=f"Disconnect error: {str(e)}")
            self.scan_button.config(state="normal")
    
    def log_message(self, message: str):
        """Add message to log area."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.logger.info(message)
        
    # Sub-GHz Operations
    def _start_subghz_record(self):
        """Start recording Sub-GHz signals."""
        try:
            freq = float(self.freq_var.get())
            mod = self.mod_var.get()
            self.log_message(f"Starting Sub-GHz recording at {freq}MHz ({mod})")
            self._queue_async_task(self.flipper.start_subghz_scan(freq, mod))
        except ValueError:
            messagebox.showerror("Error", "Invalid frequency value")
            
    def _stop_subghz_record(self):
        """Stop recording Sub-GHz signals."""
        self.log_message("Stopping Sub-GHz recording")
        self._queue_async_task(self.flipper.stop_subghz_scan())
        
    def _transmit_subghz(self):
        """Transmit recorded Sub-GHz signal."""
        if not self.current_signal or self.current_signal.mode != FlipperMode.SUB_GHZ:
            messagebox.showwarning("Warning", "No Sub-GHz signal captured")
            return
            
        self.log_message("Transmitting Sub-GHz signal")
        self._queue_async_task(self.flipper.transmit_subghz(self.current_signal))
        
    # RFID Operations
    def _read_rfid(self):
        """Read RFID card."""
        self.log_message("Reading RFID card...")
        async def read_and_update():
            signal = await self.flipper.read_rfid()
            if signal:
                self.current_signal = signal
                self.rfid_data.delete(1.0, tk.END)
                self.rfid_data.insert(tk.END, f"Protocol: {signal.protocol}\nData: {signal.data.hex()}")
                self.log_message("RFID card read successfully")
            else:
                self.log_message("Failed to read RFID card")
        self._queue_async_task(read_and_update())
        
    def _write_rfid(self):
        """Write to RFID card."""
        if not self.current_signal or self.current_signal.mode != FlipperMode.RFID:
            messagebox.showwarning("Warning", "No RFID data to write")
            return
            
        self.log_message("Writing to RFID card...")
        self._queue_async_task(self.flipper.write_rfid(self.current_signal))
        
    def _emulate_rfid(self):
        """Emulate RFID card."""
        if not self.current_signal or self.current_signal.mode != FlipperMode.RFID:
            messagebox.showwarning("Warning", "No RFID data to emulate")
            return
            
        self.log_message("Starting RFID emulation...")
        self._queue_async_task(self.flipper.emulate_rfid(self.current_signal))
        
    # NFC Operations
    def _read_nfc(self):
        """Read NFC tag."""
        self.log_message("Reading NFC tag...")
        async def read_and_update():
            signal = await self.flipper.read_nfc()
            if signal:
                self.current_signal = signal
                self.nfc_data.delete(1.0, tk.END)
                self.nfc_data.insert(tk.END, f"Protocol: {signal.protocol}\nData: {signal.data.hex()}")
                self.log_message("NFC tag read successfully")
            else:
                self.log_message("Failed to read NFC tag")
        self._queue_async_task(read_and_update())
        
    def _write_nfc(self):
        """Write to NFC tag."""
        if not self.current_signal or self.current_signal.mode != FlipperMode.NFC:
            messagebox.showwarning("Warning", "No NFC data to write")
            return
            
        self.log_message("Writing to NFC tag...")
        self._queue_async_task(self.flipper.write_nfc(self.current_signal))
        
    def _emulate_nfc(self):
        """Emulate NFC tag."""
        if not self.current_signal or self.current_signal.mode != FlipperMode.NFC:
            messagebox.showwarning("Warning", "No NFC data to emulate")
            return
            
        self.log_message("Starting NFC emulation...")
        self._queue_async_task(self.flipper.emulate_nfc(self.current_signal))
        
    # IR Operations
    def _record_ir(self):
        """Record IR signal."""
        self.log_message("Recording IR signal...")
        async def record_and_update():
            signal = await self.flipper.record_ir()
            if signal:
                self.current_signal = signal
                self.log_message("IR signal recorded successfully")
            else:
                self.log_message("Failed to record IR signal")
        self._queue_async_task(record_and_update())
        
    def _transmit_ir(self):
        """Transmit IR signal."""
        if not self.current_signal or self.current_signal.mode != FlipperMode.IR:
            messagebox.showwarning("Warning", "No IR signal to transmit")
            return
            
        self.log_message("Transmitting IR signal...")
        self._queue_async_task(self.flipper.transmit_ir(self.current_signal))
        
    def _learn_remote(self):
        """Learn IR remote control buttons."""
        self.log_message("Starting IR remote learning mode...")
        async def learn_and_update():
            signals = await self.flipper.learn_remote()
            if signals:
                self.remote_buttons.delete(1.0, tk.END)
                for i, signal in enumerate(signals, 1):
                    self.remote_buttons.insert(tk.END, f"Button {i}: {signal.protocol}\n")
                self.log_message(f"Learned {len(signals)} IR buttons")
            else:
                self.log_message("Failed to learn IR remote")
        self._queue_async_task(learn_and_update())
    
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
