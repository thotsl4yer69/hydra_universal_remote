"""Logging configuration for Hydra Universal Remote."""

from __future__ import annotations

import logging
from logging import Handler
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

class TkTextHandler(Handler):
    """Logging handler that writes to a Tkinter Text widget."""

    def __init__(self, text_widget) -> None:  # type: ignore[override]
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - GUI integration
        msg = self.format(record)
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", msg + "\n")
        self.text_widget.configure(state="disabled")
        self.text_widget.see("end")


def configure_logging(level: int = logging.INFO, *, log_file: Optional[str] = None) -> None:
    """Initialise the root logger once."""
    logger = logging.getLogger()
    if logger.handlers:
        return

    logger.setLevel(level)
    formatter = logging.Formatter(_DEFAULT_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
