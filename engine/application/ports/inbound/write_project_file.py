"""Inbound port: write content to a project file."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["WriteProjectFilePort"]


@runtime_checkable
class WriteProjectFilePort(Protocol):
    """Write raw text content to a file within a project."""

    def execute(self, project_path: Path, relative_path: str, content: str) -> None:
        """Persist the content to the file."""
        ...
