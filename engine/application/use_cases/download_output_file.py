"""Use case: Download a single generated output file."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class DownloadOutputFile:
    """Resolve and validate an output file path for download."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path, relative_path: str) -> Path:
        """Return the resolved absolute path to the output file.

        Raises OutputFileNotFoundError if the file does not exist
        or the path escapes the output directory.
        """
        logger.debug("Resolving output %s in %s", relative_path, project_path.name)
        return self._repository.resolve_output_file(project_path, relative_path)
