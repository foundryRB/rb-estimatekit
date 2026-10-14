"""Project — the aggregate root. All project data and cross-phase behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.entities.assumption import Assumption
from engine.domain.model.entities.guideline import Guideline
from engine.domain.model.entities.requirement import Requirement
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_id import PhaseId
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

__all__ = ["Project"]


@dataclass
class Project:
    """Aggregate root — the central entity that owns everything.

    Constructed by the ProjectRepository (outbound adapter). Consumed by
    use cases and passed to outbound writers for rendering. The pitch copy
    of a deck (executive summary, speaker notes) belongs to the phase it
    sells, so it lives on :class:`Phase`.
    """

    config: ProjectConfig
    phases: list[Phase] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)
    guidelines: list[Guideline] = field(default_factory=list)
    source_path: Path | None = None

    def compute_all_efforts(self) -> dict[PhaseId, PhaseEffort]:
        """Compute effort breakdown for every phase."""
        return {phase.phase_id: phase.compute_effort() for phase in self.phases}

    def schedule_all_roadmaps(self) -> list[PhaseRoadmap]:
        """Run the scheduling algorithm for every phase.

        Returns per-phase roadmaps only.  Merging into an "All" view is
        the responsibility of the use-case or adapter that needs it.
        """
        return [phase.schedule_roadmap() for phase in self.phases]

    def discover_categories(self) -> list[Category]:
        """Return unique requirement categories in encounter order."""
        from engine.domain.services.requirement_service import discover_categories

        return discover_categories(self.requirements)

    def count_requirements_per_phase(self) -> dict[PhaseId, int]:
        """Count how many requirements are allocated to each phase."""
        counts: dict[str, int] = {}
        for phase in self.phases:
            counts[phase.phase_id] = sum(
                1 for req in self.requirements if req.is_allocated_to(phase.phase_id)
            )
        return counts

    def get_phase(self, phase_id: PhaseId) -> Phase | None:
        """Find a phase by its ID."""
        for phase in self.phases:
            if phase.phase_id == phase_id:
                return phase
        return None

    def guidelines_for(self, phase_id: PhaseId) -> list[Guideline]:
        """The guidelines governing *phase_id*: the platform's and the phase's own."""
        return [g for g in self.guidelines if g.applies_to(phase_id)]
