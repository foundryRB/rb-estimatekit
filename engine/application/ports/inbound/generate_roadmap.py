"""Inbound port: generate roadmap views for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["GenerateRoadmapPort"]


@runtime_checkable
class GenerateRoadmapPort(Protocol):
    """Schedule and write roadmap views for all phases."""

    def execute(self, project_path: Path) -> int:
        """Load the project, schedule all phases, write roadmap output.

        Returns the number of roadmap files written.
        """
        ...
