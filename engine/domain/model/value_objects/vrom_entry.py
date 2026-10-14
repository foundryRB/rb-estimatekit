"""VromEntry — revenue/cost entry for VROM reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_id import PhaseId

__all__ = ["VromEntry"]


@dataclass(frozen=True)
class VromEntry:
    """Revenue/cost entry for VROM reporting."""

    phase_id: PhaseId
    revenue: float
