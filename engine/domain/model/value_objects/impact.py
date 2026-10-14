"""Impact — impact level for assumptions."""

from __future__ import annotations

from enum import Enum

__all__ = ["Impact"]


class Impact(Enum):
    """Impact level for a project assumption."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
