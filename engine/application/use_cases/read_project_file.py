"""Use case: Read a single project file."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class ReadProjectFile:
    """Read the raw content of one data file inside a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path, relative_path: str) -> str:
        """Return the text content of the file."""
        logger.debug("Reading %s from %s", relative_path, project_path.name)
        return self._repository.read_data_file(project_path, relative_path)
