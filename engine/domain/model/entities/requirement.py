"""Requirement — a single requirement from the BRD."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.requirement_id import RequirementId

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_id import PhaseId

__all__ = ["Requirement"]


@dataclass
class Requirement:
    """A single requirement from the BRD."""

    id: RequirementId
    category: Category
    description: str
    phase_allocations: dict[PhaseId, str] = field(default_factory=dict)
    # phase_id → allocation text e.g. "Full", "Manual Only", "—"

    def is_allocated_to(self, phase_id: PhaseId) -> bool:
        """Whether this requirement has non-trivial allocation in the given phase."""
        alloc = self.phase_allocations.get(phase_id, "")
        return alloc not in ("", "—", "-")
