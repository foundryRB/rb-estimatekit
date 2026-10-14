"""Inbound port: list all editable data files in a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.file_info import FileInfo

__all__ = ["ListProjectFilesPort"]


@runtime_checkable
class ListProjectFilesPort(Protocol):
    """List the data files that make up a project."""

    def execute(self, project_path: Path) -> list[FileInfo]:
        """Return metadata for every editable file."""
        ...
