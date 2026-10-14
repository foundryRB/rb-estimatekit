"""Centralized logging configuration for the EstimateKit engine.

Usage — every module::

    from engine.logging import get_logger
    logger = get_logger(__name__)

Configuration — call once at application startup (CLI or HTTP)::

    from engine.logging import configure_logging
    configure_logging(level=logging.INFO)

Design rules:
  - Single ``get_logger`` factory — no raw ``logging.getLogger``.
  - Single ``configure_logging`` call — format, level, handler in one place.
  - Domain layer may log at DEBUG; adapters at INFO.
"""

from __future__ import annotations

import logging
import sys

__all__ = ["configure_logging", "get_logger"]

_CONFIGURED = False

LOG_FORMAT = "%(asctime)s  %(levelname)-5s  %(name)s  %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.  Always use ``__name__`` as *name*."""
    return logging.getLogger(name)


def configure_logging(
    *,
    level: int = logging.INFO,
    fmt: str = LOG_FORMAT,
    date_fmt: str = LOG_DATE_FORMAT,
) -> None:
    """Configure the root logger for the engine.

    Safe to call more than once — subsequent calls are no-ops.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=date_fmt))

    root = logging.getLogger("engine")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False

    _CONFIGURED = True
