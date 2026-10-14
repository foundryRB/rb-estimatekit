"""Use case: Import data files into a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class ImportProject:
    """Import data files into a project (overwriting existing)."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path, files: dict[str, bytes]) -> None:
        """Write validated data files to the project directory.

        Extension filtering and path security checks are handled
        by the repository.
        """
        self._repository.import_data_files(project_path, files)
        logger.info("Imported %d file(s) into %s", len(files), project_path.name)
