"""Port: presentation writer — output slide decks."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_id import PhaseId
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap


class PresentationWriter(Protocol):
    """Generate a presentation deck from the project domain model."""

    def write_deck(
        self,
        project: Project,
        phase: Phase,
        efforts: dict[PhaseId, PhaseEffort],
        roadmaps: list[PhaseRoadmap],
        output_dir: Path,
    ) -> int:
        """Write the slide deck that sells *phase* to the output directory.

        The deck renders the phase's pitch, architecture and sections, with
        the project's cross-phase slides as context.
        Returns the number of slide pages written.
        """
        ...
