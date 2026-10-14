"""PhaseId — strongly-typed identifier for delivery phases."""

from __future__ import annotations

from typing import NewType

__all__ = ["PhaseId"]

PhaseId = NewType("PhaseId", str)
