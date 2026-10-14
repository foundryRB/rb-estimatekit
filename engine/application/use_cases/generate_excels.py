"""Use case: Generate Excel workbooks for a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.excel_writer import ExcelWriter
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class GenerateExcels:
    """Generate all Excel workbooks from project data."""

    def __init__(self, repository: ProjectRepository, writer: ExcelWriter) -> None:
        self._repository = repository
        self._writer = writer

    def execute(self, project_path: Path) -> int:
        """Load the project and write all Excel workbooks.

        Returns the number of workbooks written.
        """
        project = self._repository.load(project_path)
        output_dir = project_path / "output" / "excel"
        count = self._writer.write_all(project, output_dir)
        logger.info("Wrote %d Excel workbook(s) for %s", count, project_path.name)
        return count
