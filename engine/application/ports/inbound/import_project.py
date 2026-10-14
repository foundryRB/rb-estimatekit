"""Inbound port: import data files into a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["ImportProjectPort"]


@runtime_checkable
class ImportProjectPort(Protocol):
    """Import data files into a project (overwriting existing)."""

    def execute(self, project_path: Path, files: dict[str, bytes]) -> None:
        """Write validated data files to the project directory."""
        ...
