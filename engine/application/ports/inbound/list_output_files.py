"""Inbound port: list generated output files for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.output_file_info import OutputFileInfo

__all__ = ["ListOutputFilesPort"]


@runtime_checkable
class ListOutputFilesPort(Protocol):
    """List the generated output files for a project."""

    def execute(self, project_path: Path) -> list[OutputFileInfo]:
        """Return metadata for every output file."""
        ...
