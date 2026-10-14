"""Inbound port: discover projects under a root directory."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.discovered_project import DiscoveredProject

__all__ = ["DiscoverProjectsPort"]


@runtime_checkable
class DiscoverProjectsPort(Protocol):
    """Find all valid projects under a root directory."""

    def execute(self, projects_root: Path) -> list[DiscoveredProject]:
        """Return every discovered project with its archived state."""
        ...
