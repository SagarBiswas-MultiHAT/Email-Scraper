"""Logging helpers."""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging once for CLI usage."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)


def get_logger() -> logging.Logger:
    """Return the module logger used across the package."""
    return logging.getLogger("email_harvester")
