"""ProjectSummary — lightweight read-only overview of a project."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.phase_id import PhaseId

__all__ = ["ProjectSummary"]


@dataclass(frozen=True)
class ProjectSummary:
    """Lightweight overview of a project — no heavy scheduling."""

    name: str
    client: str
    description: str
    phase_count: int
    requirement_count: int
    assumption_count: int
    archived: bool
    phases: list[PhaseId] = field(default_factory=list)
    """The defined phase ids in phase-table order; a deck is built for one of them."""
