"""Confidence — confidence level for assumptions."""

from __future__ import annotations

from enum import Enum

__all__ = ["Confidence"]


class Confidence(Enum):
    """Confidence level for a project assumption."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
