"""Port: project repository — persistence operations for projects."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.data_file_export import DataFileExport
from engine.domain.model.value_objects.file_info import FileInfo
from engine.domain.model.value_objects.output_file_info import OutputFileInfo

__all__ = ["ProjectRepository"]


class ProjectRepository(Protocol):
    """Persistence contract for project data.

    Abstracts away storage specifics (filesystem, database, etc.).
    Use cases depend on this protocol; outbound adapters implement it.
    """

    def load(self, project_path: Path) -> Project:
        """Load all project data and construct the aggregate root."""
        ...

    def exists(self, project_path: Path) -> bool:
        """Check whether a valid project exists at the given path."""
        ...

    def delete(self, project_path: Path) -> None:
        """Delete a project directory and all its contents.

        Raises ProjectNotFoundError if no valid project exists at the path.
        """
        ...

    def rename(self, project_path: Path, new_project_path: Path) -> None:
        """Move a project directory to a new path in one atomic rename.

        Raises ProjectNotFoundError if no valid project exists at the source
        path, and ProjectAlreadyExistsError if the target path is occupied.
        """
        ...

    def is_archived(self, project_path: Path) -> bool:
        """Check whether the project at the given path is archived."""
        ...

    def set_archived(self, project_path: Path, *, archived: bool) -> None:
        """Mark or unmark a project as archived.

        Raises ProjectNotFoundError if no valid project exists at the path.
        """
        ...

    def discover(self, projects_root: Path) -> list[Path]:
        """Find all project directories under a root path."""
        ...

    def load_config(self, project_path: Path) -> ProjectConfig:
        """Load only the project config (project.yaml), without the data files.

        Raises ProjectNotFoundError if no valid project exists at the path.
        """
        ...

    def save_config(self, project_path: Path, config: ProjectConfig) -> None:
        """Persist the project config (e.g., project.yaml)."""
        ...

    def list_data_files(self, project_path: Path) -> list[FileInfo]:
        """List all editable data files in the project."""
        ...

    def read_data_file(self, project_path: Path, relative_path: str) -> str:
        """Read the raw text content of a data file."""
        ...

    def write_data_file(
        self, project_path: Path, relative_path: str, content: str,
    ) -> None:
        """Write raw text content to a data file."""
        ...

    def read_data_file_exact(self, project_path: Path, relative_path: str) -> str:
        """Read a data file's text with its line endings as stored."""
        ...

    def write_data_file_exact(
        self, project_path: Path, relative_path: str, content: str,
    ) -> None:
        """Write text to a data file exactly as given, line endings untranslated."""
        ...

    def delete_data_file(self, project_path: Path, relative_path: str) -> None:
        """Delete a data file from the project.

        Raises InvalidPathError if the path escapes the project directory,
        and DataFileNotFoundError if no deletable data file exists there.
        """
        ...

    def list_output_files(self, project_path: Path) -> list[OutputFileInfo]:
        """List all generated output files for the project."""
        ...

    def resolve_output_file(self, project_path: Path, relative_path: str) -> Path:
        """Resolve and validate an output file path.

        Returns the absolute path to the output file.
        Raises OutputFileNotFoundError if the file does not exist or
        the path escapes the output directory.
        """
        ...

    def export_data_files(self, project_path: Path) -> list[DataFileExport]:
        """Read all data files and return their paths and raw content."""
        ...

    def import_data_files(
        self, project_path: Path, files: dict[str, bytes],
    ) -> None:
        """Write data files from a mapping of relative paths to raw content.

        Only files with allowed data extensions are written. Paths that
        escape the project directory are silently skipped.
        """
        ...
