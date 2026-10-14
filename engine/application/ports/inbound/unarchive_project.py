"""Inbound port: unarchive a project, returning it to the active listing."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["UnarchiveProjectPort"]


@runtime_checkable
class UnarchiveProjectPort(Protocol):
    """Unarchive a project: return it to the active listing."""

    def execute(self, projects_root: Path, slug: str) -> Path:
        """Unarchive the project at *projects_root/slug*. Returns its path."""
        ...
