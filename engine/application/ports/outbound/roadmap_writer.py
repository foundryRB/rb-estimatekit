"""Port: roadmap writer — output roadmap views to persistent storage."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap


class RoadmapWriter(Protocol):
    """Write roadmap scheduling results to output files."""

    def write_phase(self, output_dir: Path, roadmap: PhaseRoadmap) -> None:
        """Write all four views for a single phase."""
        ...

    def write_merged(self, output_dir: Path, roadmaps: list[PhaseRoadmap]) -> None:
        """Write the merged all-phases view."""
        ...
