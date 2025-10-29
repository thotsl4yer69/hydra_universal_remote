"""Compatibility wrapper for legacy Flipper USB interface.

Provides the synchronous API that existing tooling expects by internally
leveraging the new asynchronous ``FlipperUSBTransport`` implementation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from .flipper_transport import FlipperUSBTransport

logger = logging.getLogger(__name__)


class FlipperUSB:
    """Synchronous facade around :class:`FlipperUSBTransport`."""

    def __init__(self) -> None:
        self._transport = FlipperUSBTransport()

    @staticmethod
    def find_flipper_ports() -> List[str]:
        """Return a list of detected Flipper Zero USB device ports."""
        detected = FlipperUSBTransport.find_flipper_port()
        if not detected:
            return []
        port, _ = detected
        return [port]

    def connect(self, port: Optional[str] = None) -> bool:
        """Connect to the Flipper Zero over USB."""
        try:
            return asyncio.run(self._transport.connect(port=port))
        except Exception as exc:  # pragma: no cover - defensive log
            logger.error("Legacy USB connect failed: %s", exc)
            return False

    def disconnect(self) -> bool:
        """Disconnect from the Flipper Zero device."""
        try:
            return asyncio.run(self._transport.disconnect())
        except Exception as exc:  # pragma: no cover - defensive log
            logger.error("Legacy USB disconnect failed: %s", exc)
            return False

    def send_command(self, data: bytes) -> bool:
        """Send raw bytes to the device."""
        try:
            written = asyncio.run(self._transport.write(data))
            return written == len(data)
        except Exception as exc:  # pragma: no cover - defensive log
            logger.error("Legacy USB send failed: %s", exc)
            return False

    def read_response(self, size: int = -1, timeout: float | None = 1.0) -> bytes:
        """Read bytes from the device."""
        try:
            return asyncio.run(self._transport.read(size=size, timeout=timeout))
        except Exception as exc:  # pragma: no cover - defensive log
            logger.error("Legacy USB read failed: %s", exc)
            return b""
