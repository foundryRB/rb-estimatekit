"""Use case: Generate roadmap views for a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.application.ports.outbound.roadmap_writer import RoadmapWriter
from engine.logging import get_logger

logger = get_logger(__name__)


class GenerateRoadmap:
    """Schedule and write roadmap views for all phases."""

    def __init__(self, repository: ProjectRepository, writer: RoadmapWriter) -> None:
        self._repository = repository
        self._writer = writer

    def execute(self, project_path: Path) -> int:
        """Load the project, schedule all phases, write roadmap output.

        Returns the number of roadmap files written.
        """
        project = self._repository.load(project_path)
        output_dir = project_path / "output" / "roadmap"

        roadmaps = project.schedule_all_roadmaps()

        count = 0
        for roadmap in roadmaps:
            self._writer.write_phase(output_dir, roadmap)
            count += 1

        if roadmaps:
            self._writer.write_merged(output_dir, roadmaps)
            count += 1

        logger.info("Wrote %d roadmap file(s) for %s", count, project_path.name)
        return count
