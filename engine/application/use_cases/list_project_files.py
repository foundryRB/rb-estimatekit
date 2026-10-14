"""Use case: List data files in a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.model.value_objects.file_info import FileInfo
from engine.logging import get_logger

logger = get_logger(__name__)


class ListProjectFiles:
    """List every editable data file in a project directory."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path) -> list[FileInfo]:
        """Return metadata for every data file in the project."""
        files = self._repository.list_data_files(project_path)
        logger.debug("Listed %d data file(s) in %s", len(files), project_path.name)
        return files
