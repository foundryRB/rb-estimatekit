"""Inbound port: generate the slide deck for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["GenerateSlidesPort"]


@runtime_checkable
class GenerateSlidesPort(Protocol):
    """Generate the presentation deck that sells one phase."""

    def execute(self, project_path: Path, *, phase: str | None = None) -> int:
        """Load project, schedule roadmaps, write the deck for *phase*.

        Returns the number of slide pages written.
        """
        ...
