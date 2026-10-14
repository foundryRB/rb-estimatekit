"""Inbound port: delete a project file."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["DeleteProjectFilePort"]


@runtime_checkable
class DeleteProjectFilePort(Protocol):
    """Delete a data file within a project."""

    def execute(self, project_path: Path, relative_path: str) -> None:
        """Remove the file at the given project-relative path."""
        ...
