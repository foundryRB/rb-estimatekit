"""Inbound port: get a read-only summary of a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.project_summary import ProjectSummary

__all__ = ["GetProjectSummaryPort"]


@runtime_checkable
class GetProjectSummaryPort(Protocol):
    """Load a project and return a lightweight summary."""

    def execute(self, project_path: Path) -> ProjectSummary:
        """Load the project and extract summary information."""
        ...
