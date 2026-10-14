"""CellMarker — markers used in roadmap grid cells."""

from __future__ import annotations

from enum import Enum

__all__ = ["CellMarker"]


class CellMarker(Enum):
    """Markers used in roadmap grid cells."""

    EMPTY = ""
    ACTIVE = "·"
    MILESTONE = "◆"
    DESIGN = "D"
    TEST_ACTIVE = "T"
    TEST_MILESTONE = "▲"
