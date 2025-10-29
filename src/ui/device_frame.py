"""Device connection frame for Hydra Universal Remote GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import logging

from ..core.runtime import runtime
from ..device.device_manager import ConnectionStatus, ConnectionType, DeviceManager

logger = logging.getLogger(__name__)

class DeviceConnectionFrame(ttk.LabelFrame):
    """Frame for device connection controls."""
    
    def __init__(self, master, device_manager: DeviceManager,
                 on_connection_changed: Optional[Callable] = None):
        """Initialize connection frame.
        
        Args:
            master: Parent widget
            device_manager: Device manager instance
            on_connection_changed: Optional callback for connection state changes
        """
        super().__init__(master, text="Device Connection")
        self.device_manager = device_manager
        self._runtime = runtime
        self.on_connection_changed = on_connection_changed
        
        # Add callback for status updates
        self.device_manager.add_status_callback(self._on_status_changed)
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Connection type selection
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="Connection:").pack(side=tk.LEFT)
        
        self.connection_type = tk.StringVar(value="auto")
        ttk.Radiobutton(
            type_frame,
            text="Auto",
            value="auto",
            variable=self.connection_type
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_frame,
            text="USB",
            value="usb",
            variable=self.connection_type
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_frame,
            text="BLE",
            value="ble",
            variable=self.connection_type
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            type_frame,
            text="Mock",
            value="mock",
            variable=self.connection_type
        ).pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Disconnected")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Device info
        self.info_text = tk.Text(
            self,
            height=3,
            width=30,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.scan_button = ttk.Button(
            button_frame,
            text="Scan",
            command=lambda: self._run_async(self._scan_devices())
        )
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = ttk.Button(
            button_frame,
            text="Connect",
            command=lambda: self._run_async(self._toggle_connection()),
            state=tk.DISABLED
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.test_button = ttk.Button(
            button_frame,
            text="Test",
            command=lambda: self._run_async(self._test_connection()),
            state=tk.DISABLED
        )
        self.test_button.pack(side=tk.LEFT, padx=5)

    def destroy(self):  # pragma: no cover - GUI cleanup
        self.device_manager.remove_status_callback(self._on_status_changed)
        super().destroy()

    def _run_async(self, coro):
        """Execute coroutine on the shared runtime and handle logging."""
        future = self._runtime.run_in_background(coro)

        def _callback(_):
            try:
                future.result()
            except Exception as exc:
                logger.error("Async operation failed: %s", exc)

        future.add_done_callback(lambda f: self.after(0, _callback, f))
        
    async def _scan_devices(self):
        """Scan for available devices."""
        self._set_buttons_state(tk.DISABLED)
        self.status_label.configure(text="Scanning...")
        
        try:
            devices = await self.device_manager.scan_devices()
            
            # Update info text
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            
            if devices["usb"]:
                self.info_text.insert(tk.END, f"USB: {devices['usb']['port']}\n")
            if devices["ble"]:
                self.info_text.insert(tk.END, f"BLE: {devices['ble']['address']}\n")
            if devices.get("mock"):
                self.info_text.insert(tk.END, "Mock transport available\n")
                
            if not (devices["usb"] or devices["ble"]):
                self.info_text.insert(tk.END, "No devices found")
                
            self.info_text.configure(state=tk.DISABLED)
            
            # Enable connect button if devices found
            if devices["usb"] or devices["ble"] or devices.get("mock"):
                self.connect_button.configure(state=tk.NORMAL)
                
        except Exception as e:
            logger.error(f"Scan error: {e}")
            self.status_label.configure(text="Scan failed")
            
        finally:
            self._set_buttons_state(tk.NORMAL)
            
    async def _toggle_connection(self):
        """Handle connect/disconnect."""
        if self.device_manager.is_connected():
            await self._disconnect()
        else:
            await self._connect()
            
    async def _connect(self):
        """Connect to device."""
        self._set_buttons_state(tk.DISABLED)
        self.status_label.configure(text="Connecting...")
        
        try:
            # Determine connection type
            conn_type = self.connection_type.get()
            devices = await self.device_manager.scan_devices()
            
            if conn_type == "auto":
                if devices["usb"]:
                    success = await self.device_manager.connect(
                        ConnectionType.USB,
                        port=devices["usb"]["port"]
                    )
                elif devices["ble"]:
                    success = await self.device_manager.connect(
                        ConnectionType.BLE,
                        address=devices["ble"]["address"]
                    )
                else:
                    success = await self.device_manager.connect(ConnectionType.MOCK)

            elif conn_type == "usb":
                if not devices["usb"]:
                    raise RuntimeError("No USB device found")
                success = await self.device_manager.connect(
                    ConnectionType.USB,
                    port=devices["usb"]["port"]
                )
                
            elif conn_type == "ble":
                if not devices["ble"]:
                    raise RuntimeError("No BLE device found")
                success = await self.device_manager.connect(
                    ConnectionType.BLE,
                    address=devices["ble"]["address"]
                )

            else:  # Mock
                success = await self.device_manager.connect(ConnectionType.MOCK)
                
            if success:
                self.connect_button.configure(text="Disconnect")
                self.test_button.configure(state=tk.NORMAL)
                if self.on_connection_changed:
                    self.on_connection_changed(True)
            else:
                raise RuntimeError("Connection failed")
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.status_label.configure(text="Connection failed")
            
        finally:
            self._set_buttons_state(tk.NORMAL)
            
    async def _disconnect(self):
        """Disconnect from device."""
        try:
            await self.device_manager.disconnect()
            self.connect_button.configure(text="Connect")
            self.test_button.configure(state=tk.DISABLED)
            if self.on_connection_changed:
                self.on_connection_changed(False)
                
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            
    async def _test_connection(self):
        """Test current connection."""
        self._set_buttons_state(tk.DISABLED)
        self.status_label.configure(text="Testing...")
        
        try:
            success, message = await self.device_manager.test_connection()
            self.status_label.configure(
                text="Test passed" if success else "Test failed"
            )
            
            # Update info text
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, message)
            self.info_text.configure(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Test error: {e}")
            self.status_label.configure(text="Test error")
            
        finally:
            self._set_buttons_state(tk.NORMAL)
            
    def _set_buttons_state(self, state: str):
        """Set state of all buttons."""
        self.scan_button.configure(state=state)
        self.connect_button.configure(state=state)
        if self.device_manager.is_connected():
            self.test_button.configure(state=state)
        else:
            self.test_button.configure(state=tk.DISABLED)
            
    def _on_status_changed(self, status: ConnectionStatus):
        """Handle device status changes."""
        def _update():
            status_text = status.value.title()
            self.status_label.configure(text=status_text)

            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)

            if status == ConnectionStatus.CONNECTED:
                info = self.device_manager.get_connection_info()
                if info:
                    for key, value in info.items():
                        self.info_text.insert(tk.END, f"{key}: {value}\n")

            self.info_text.configure(state=tk.DISABLED)

        self.after(0, _update)