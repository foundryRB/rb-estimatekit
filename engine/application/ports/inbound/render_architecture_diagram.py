"""Inbound port: render one architecture diagram to SVG."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["RenderArchitectureDiagramPort"]


@runtime_checkable
class RenderArchitectureDiagramPort(Protocol):
    """Render a named architecture diagram to an SVG document."""

    def execute(self, project_path: Path, name: str) -> str:
        """Return the SVG document for the named diagram."""
        ...
