"""Inbound port: archive a project, parking it out of the active listing."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["ArchiveProjectPort"]


@runtime_checkable
class ArchiveProjectPort(Protocol):
    """Archive a project: keep all data, drop it from the active listing."""

    def execute(self, projects_root: Path, slug: str) -> Path:
        """Archive the project at *projects_root/slug*. Returns its path."""
        ...
