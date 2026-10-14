"""Guideline — an architecture guideline / design principle."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ALL_PHASES", "Guideline"]

ALL_PHASES = "All"
"""The ``Phase IDs`` value of a guideline that governs every phase."""


@dataclass
class Guideline:
    """An architecture guideline / design principle.

    ``phase_ids`` says which phases it governs: ``All`` for a principle of the
    platform, or the ids of the phases whose decision it records. A phase's deck
    renders the guidelines that apply to it and no other phase's.
    """

    guideline_id: str
    group: str
    name: str
    description: str
    phase_ids: frozenset[str] = field(default_factory=lambda: frozenset({ALL_PHASES}))

    def applies_to(self, phase_id: str) -> bool:
        """Whether this guideline governs *phase_id*."""
        return any(p == phase_id or p.lower() == ALL_PHASES.lower() for p in self.phase_ids)
