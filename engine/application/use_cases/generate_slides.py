"""Use case: Generate the slide deck for a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.presentation_writer import PresentationWriter
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.application.ports.outbound.roadmap_writer import RoadmapWriter
from engine.domain.services.phase_selection import select_phase_with_pitch
from engine.domain.services.roadmap_merger import merge_roadmaps
from engine.logging import get_logger

logger = get_logger(__name__)


class GenerateSlides:
    """Generate the Slidev presentation deck that sells one phase.

    Requires roadmaps to already be scheduled (for the Gantt slides).
    """

    def __init__(
        self,
        repository: ProjectRepository,
        roadmap_writer: RoadmapWriter,
        presentation_writer: PresentationWriter,
    ) -> None:
        self._repository = repository
        self._roadmap_writer = roadmap_writer
        self._presentation_writer = presentation_writer

    def execute(self, project_path: Path, *, phase: str | None = None) -> int:
        """Load project, schedule roadmaps, write the deck for *phase*.

        Returns the number of slide pages written.
        """
        project = self._repository.load(project_path)
        sold = select_phase_with_pitch(project, phase)
        output_dir = project_path / "output" / "slides"

        roadmaps = project.schedule_all_roadmaps()
        efforts = project.compute_all_efforts()

        # Slides need a merged "All" PhaseRoadmap for overall Gantt charts
        slide_roadmaps = (
            roadmaps + [merge_roadmaps(roadmaps)]
            if len(roadmaps) >= 2
            else list(roadmaps)
        )
        count = self._presentation_writer.write_deck(
            project, sold, efforts, slide_roadmaps, output_dir,
        )
        logger.info(
            "Wrote %d slide page(s) for %s (%s)", count, project_path.name, sold.phase_id,
        )
        return count
