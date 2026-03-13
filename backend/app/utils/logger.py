"""Simple logging helpers."""

import logging


def configure_logging() -> None:
    """Configure a simple app-wide logger format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for one module."""
    return logging.getLogger(name)
