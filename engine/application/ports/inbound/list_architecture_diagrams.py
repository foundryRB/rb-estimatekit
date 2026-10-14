"""Inbound port: list a project's architecture diagram sources."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.file_info import FileInfo

__all__ = ["ListArchitectureDiagramsPort"]


@runtime_checkable
class ListArchitectureDiagramsPort(Protocol):
    """List the PlantUML diagram sources in a project's architecture data."""

    def execute(self, project_path: Path) -> list[FileInfo]:
        """Return metadata for every architecture diagram source."""
        ...
