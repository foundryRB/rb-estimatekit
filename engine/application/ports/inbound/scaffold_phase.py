"""Inbound port: mint a new phase in an existing project from the templates."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["ScaffoldPhasePort"]


@runtime_checkable
class ScaffoldPhasePort(Protocol):
    """Add a phase's row, matrix column and example-marked file set to a project."""

    def execute(self, project_path: Path, phase_id: str, *, force: bool = False) -> list[str]:
        """Mint *phase_id*. Returns the project-relative paths written."""
        ...
