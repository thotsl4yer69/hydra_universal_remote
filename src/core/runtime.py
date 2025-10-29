"""Runtime helpers for coordinating asyncio with Tkinter."""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Awaitable, Callable
from typing import Any, Optional

logger = logging.getLogger(__name__)

class AsyncRuntime:
    """Background asyncio runtime for GUI integrations."""

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def ensure_started(self) -> asyncio.AbstractEventLoop:
        """Start the background event loop if needed."""
        with self._lock:
            if self._loop and self._loop.is_running():
                return self._loop

            loop = asyncio.new_event_loop()
            thread = threading.Thread(target=self._run_loop, args=(loop,), daemon=True)
            thread.start()
            self._loop = loop
            self._thread = thread
            return loop

    def _run_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Async loop crashed")
        finally:
            loop.close()

    def run_in_background(self, coro: Awaitable[Any], *, name: str | None = None) -> asyncio.Future:
        """Schedule a coroutine on the runtime and return its future."""
        loop = self.ensure_started()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        if name:
            future._name = name  # type: ignore[attr-defined]
        return future

    def call_soon(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Schedule a callback safely on the loop."""
        loop = self.ensure_started()
        loop.call_soon_threadsafe(func, *args, **kwargs)

    def shutdown(self, *, wait: bool = True) -> None:
        """Stop the runtime loop and join the thread."""
        with self._lock:
            if not self._loop:
                return

            loop = self._loop
            if loop.is_running():
                loop.call_soon_threadsafe(loop.stop)

            if wait and self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)

            self._loop = None
            self._thread = None

runtime = AsyncRuntime()
"""Module-level runtime singleton."""
