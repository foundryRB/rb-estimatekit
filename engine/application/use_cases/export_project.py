"""Use case: Export all project data files for archival."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.model.value_objects.data_file_export import DataFileExport
from engine.logging import get_logger

logger = get_logger(__name__)


class ExportProject:
    """Export all data files from a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path) -> list[DataFileExport]:
        """Return every data file's relative path and raw content."""
        entries = self._repository.export_data_files(project_path)
        logger.debug("Exported %d data file(s) from %s", len(entries), project_path.name)
        return entries
