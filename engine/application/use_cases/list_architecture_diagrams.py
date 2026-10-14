"""Use case: List a project's architecture diagram sources."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.constants.files.inputs import ARCHITECTURE_DATA_DIR, SUFFIX_DIAGRAM
from engine.domain.model.value_objects.file_info import FileInfo
from engine.logging import get_logger

logger = get_logger(__name__)


class ListArchitectureDiagrams:
    """List the PlantUML diagram sources in a project's architecture directory."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path) -> list[FileInfo]:
        """Return metadata for every architecture diagram source."""
        files = self._repository.list_data_files(project_path)
        diagrams = [
            f
            for f in files
            if f.directory == ARCHITECTURE_DATA_DIR and f.name.endswith(SUFFIX_DIAGRAM)
        ]
        logger.debug(
            "Listed %d architecture diagram(s) in %s", len(diagrams), project_path.name
        )
        return diagrams
