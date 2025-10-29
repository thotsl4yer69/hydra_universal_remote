"""Mock transport for development without hardware."""

from __future__ import annotations

import asyncio
from typing import Any

from .flipper_transport import FlipperTransport, TransportStatus


class MockTransport(FlipperTransport):
    """Simple in-memory transport used for demos and tests."""

    name = "mock"

    def __init__(self) -> None:
        self._connected = False
        self._buffer = bytearray()

    @classmethod
    def availability(cls) -> TransportStatus:
        return TransportStatus(True)

    async def connect(self, **kwargs: Any) -> bool:  # pragma: no cover - trivial
        await asyncio.sleep(0.05)
        self._connected = True
        return True

    async def disconnect(self) -> bool:  # pragma: no cover - trivial
        await asyncio.sleep(0.01)
        self._connected = False
        self._buffer.clear()
        return True

    async def write(self, data: bytes) -> int:
        if not self._connected:
            raise ConnectionError("Mock transport not connected")
        self._buffer.extend(data)
        return len(data)

    async def read(self, size: int = -1, timeout: float | None = None) -> bytes:
        if not self._connected:
            raise ConnectionError("Mock transport not connected")
        await asyncio.sleep(0.05)
        if not self._buffer:
            return b"OK"
        data = bytes(self._buffer[:size if size > 0 else None])
        if size > 0:
            del self._buffer[:size]
        else:
            self._buffer.clear()
        return data
