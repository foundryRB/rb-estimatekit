"""Port: Excel writer — output Excel workbooks."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from engine.domain.model.aggregates.project import Project


class ExcelWriter(Protocol):
    """Generate Excel workbooks from the project domain model."""

    def write_all(self, project: Project, output_dir: Path) -> int:
        """Write all Excel workbooks to the output directory.

        Returns the number of workbooks written.
        """
        ...
