"""Inbound port: generate Excel workbooks for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["GenerateExcelsPort"]


@runtime_checkable
class GenerateExcelsPort(Protocol):
    """Generate all Excel workbooks from project data."""

    def execute(self, project_path: Path) -> int:
        """Load the project and write all Excel workbooks. Returns the number of workbooks written.
        """
        ...
