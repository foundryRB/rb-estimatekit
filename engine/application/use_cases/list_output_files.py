"""Use case: List generated output files for a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.model.value_objects.output_file_info import OutputFileInfo
from engine.logging import get_logger

logger = get_logger(__name__)


class ListOutputFiles:
    """List all generated output artefacts for a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path) -> list[OutputFileInfo]:
        """Return metadata for every output file."""
        outputs = self._repository.list_output_files(project_path)
        logger.debug("Listed %d output file(s) in %s", len(outputs), project_path.name)
        return outputs
