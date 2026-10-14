"""Inbound port: export all project data files for archival."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.data_file_export import DataFileExport

__all__ = ["ExportProjectPort"]


@runtime_checkable
class ExportProjectPort(Protocol):
    """Export all data files from a project."""

    def execute(self, project_path: Path) -> list[DataFileExport]:
        """Return every data file's relative path and raw content."""
        ...
