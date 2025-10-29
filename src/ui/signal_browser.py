"""Signal browser GUI for Hydra Universal Remote.

Provides a graphical interface for browsing, viewing, and selecting signals.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, Callable
import logging
from ..utils.signal_library import SignalLibrary, SignalMetadata
from ttkthemes import ThemedTk

logger = logging.getLogger(__name__)

class SignalBrowserFrame(ttk.Frame):
    """Main frame for signal browsing interface."""
    
    def __init__(self, master: ThemedTk, signal_library: SignalLibrary,
                 on_signal_selected: Optional[Callable] = None):
        """Initialize signal browser frame.
        
        Args:
            master: Parent window
            signal_library: Signal library instance
            on_signal_selected: Optional callback for signal selection
        """
        super().__init__(master)
        self.signal_library = signal_library
        self.on_signal_selected = on_signal_selected
        self.selected_category = tk.StringVar()
        self.search_text = tk.StringVar()
        self.search_text.trace_add('write', self._on_search_changed)
        
        self._init_ui()
        self._load_categories()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Left side - Categories
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Categories").pack(anchor=tk.W)
        self.category_list = ttk.Treeview(
            left_frame, show="tree", selectmode="browse"
        )
        self.category_list.pack(fill=tk.Y, expand=True)
        self.category_list.bind('<<TreeviewSelect>>', self._on_category_selected)
        
        # Right side - Signals
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search bar
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        ttk.Entry(
            search_frame,
            textvariable=self.search_text
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Signal list
        self.signal_tree = ttk.Treeview(
            right_frame,
            columns=("freq", "mod", "proto"),
            show="headings"
        )
        self.signal_tree.heading("freq", text="Frequency (MHz)")
        self.signal_tree.heading("mod", text="Modulation")
        self.signal_tree.heading("proto", text="Protocol")
        
        # Scrollbar for signal list
        scrollbar = ttk.Scrollbar(
            right_frame,
            orient=tk.VERTICAL,
            command=self.signal_tree.yview
        )
        self.signal_tree.configure(yscrollcommand=scrollbar.set)
        
        self.signal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Signal details
        details_frame = ttk.LabelFrame(right_frame, text="Signal Details")
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.details_text = tk.Text(
            details_frame,
            height=5,
            width=50,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Bind signal selection
        self.signal_tree.bind('<<TreeviewSelect>>', self._on_signal_selected)
        
    def _load_categories(self):
        """Load categories into category tree."""
        self.category_list.delete(*self.category_list.get_children())
        
        # Add "All Signals" category
        self.category_list.insert(
            "",
            "end",
            "all",
            text="All Signals"
        )
        
        # Add each category
        for category in self.signal_library.get_categories():
            self.category_list.insert(
                "",
                "end",
                category,
                text=category.title()
            )
            
        # Select "All Signals" by default
        self.category_list.selection_set("all")
        self._on_category_selected()
        
    def _on_category_selected(self, event=None):
        """Handle category selection."""
        selected = self.category_list.selection()
        if not selected:
            return
            
        category_id = selected[0]
        if category_id == "all":
            # Show all signals
            signals = []
            for category in self.signal_library.get_categories():
                signals.extend(self.signal_library.get_signals_in_category(category))
        else:
            # Show signals in selected category
            signals = self.signal_library.get_signals_in_category(category_id)
            
        self._update_signal_list(signals)
        
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        search_text = self.search_text.get().strip()
        if not search_text:
            # If search is empty, show current category
            self._on_category_selected()
            return
            
        # Search across all signals
        signals = self.signal_library.search_signals(text=search_text)
        self._update_signal_list(signals)
        
    def _update_signal_list(self, signals):
        """Update signal list with provided signals."""
        self.signal_tree.delete(*self.signal_tree.get_children())
        
        for signal in signals:
            self.signal_tree.insert(
                "",
                "end",
                signal.name,
                values=(
                    f"{signal.frequency:.2f}",
                    signal.modulation,
                    signal.protocol or "Unknown"
                )
            )
            
    def _on_signal_selected(self, event=None):
        """Handle signal selection."""
        selected = self.signal_tree.selection()
        if not selected:
            return
            
        signal_name = selected[0]
        signal_meta = self.signal_library.signals.get(signal_name)
        if not signal_meta:
            return
            
        # Update details text
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = [
            f"Name: {signal_meta.name}",
            f"Category: {signal_meta.category}",
            f"Frequency: {signal_meta.frequency:.2f} MHz",
            f"Modulation: {signal_meta.modulation}",
            f"Protocol: {signal_meta.protocol or 'Unknown'}"
        ]
        
        if signal_meta.description:
            details.append(f"\nDescription: {signal_meta.description}")
            
        if signal_meta.tags:
            details.append(f"\nTags: {', '.join(signal_meta.tags)}")
            
        self.details_text.insert(tk.END, "\n".join(details))
        self.details_text.configure(state=tk.DISABLED)
        
        # Call selection callback if provided
        if self.on_signal_selected:
            signal = self.signal_library.get_signal(signal_name)
            if signal:
                self.on_signal_selected(signal)
                
    def reload(self):
        """Reload signal library data."""
        self._load_categories()
        
class SignalBrowserDialog(tk.Toplevel):
    """Dialog window for signal browsing and selection."""
    
    def __init__(self, parent: tk.Tk, signal_library: SignalLibrary):
        """Initialize signal browser dialog.
        
        Args:
            parent: Parent window
            signal_library: Signal library instance
        """
        super().__init__(parent)
        self.signal_library = signal_library
        self.selected_signal = None
        
        self.title("Signal Browser")
        self.geometry("800x600")
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize dialog UI."""
        # Main browser frame
        self.browser = SignalBrowserFrame(
            self,
            self.signal_library,
            self._on_signal_selected
        )
        self.browser.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Select",
            command=self._on_select
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT)
        
    def _on_signal_selected(self, signal):
        """Handle signal selection."""
        self.selected_signal = signal
        
    def _on_select(self):
        """Handle select button."""
        if not self.selected_signal:
            messagebox.showwarning(
                "No Selection",
                "Please select a signal first."
            )
            return
            
        self.destroy()
        
    def _on_cancel(self):
        """Handle cancel button."""
        self.selected_signal = None
        self.destroy()
        
    @classmethod
    def browse_signal(cls, parent: tk.Tk,
                     signal_library: SignalLibrary) -> Optional[SignalMetadata]:
        """Show signal browser dialog.
        
        Args:
            parent: Parent window
            signal_library: Signal library instance
            
        Returns:
            Selected signal or None if cancelled
        """
        dialog = cls(parent, signal_library)
        dialog.transient(parent)
        dialog.grab_set()
        parent.wait_window(dialog)
        return dialog.selected_signal