"""Inbound port: scaffold a new project from templates."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["ScaffoldProjectPort"]


@runtime_checkable
class ScaffoldProjectPort(Protocol):
    """Create a new project directory with all template files."""

    def execute(
        self,
        projects_root: Path,
        slug: str,
        *,
        force: bool = False,
    ) -> Path:
        """Scaffold a new project. Returns the path to the created project."""
        ...
