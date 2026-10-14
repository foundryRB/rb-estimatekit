"""Inbound port: read a single file's raw content."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["ReadProjectFilePort"]


@runtime_checkable
class ReadProjectFilePort(Protocol):
    """Read the raw text content of a file within a project."""

    def execute(self, project_path: Path, relative_path: str) -> str:
        """Return the file's text content."""
        ...
