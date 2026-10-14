"""Inbound port: delete a project and all its data."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["DeleteProjectPort"]


@runtime_checkable
class DeleteProjectPort(Protocol):
    """Delete a project directory and all its contents."""

    def execute(self, projects_root: Path, slug: str) -> Path:
        """Delete the project. Returns the path that was removed."""
        ...
