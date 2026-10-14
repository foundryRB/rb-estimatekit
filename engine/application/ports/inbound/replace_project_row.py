"""Inbound port: replace one row of a project's TSV data file by its ID."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["ReplaceProjectRowPort"]


@runtime_checkable
class ReplaceProjectRowPort(Protocol):
    """Replace the one row of a TSV data file whose ID column holds a given ID."""

    def execute(
        self, project_path: Path, relative_path: str, row_id: str, row: dict[str, str]
    ) -> None:
        """Replace the row whose ID is *row_id* with *row*."""
        ...
