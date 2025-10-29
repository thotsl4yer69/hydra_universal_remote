"""Device integration helpers (BLE / Flipper) for hydra_universal_remote.

This package contains lightweight adapters that import optional runtime
dependencies (like `bleak`) lazily so the rest of the project can be
imported/tested without hardware-capable packages installed.
"""

__all__ = ["ble_adapter", "example"]
