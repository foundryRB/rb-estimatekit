"""Inbound port: append rows to a project's TSV data file."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["AppendProjectRowsPort"]


@runtime_checkable
class AppendProjectRowsPort(Protocol):
    """Append rows to a TSV data file, each row validated against its header."""

    def execute(
        self, project_path: Path, relative_path: str, rows: list[dict[str, str]]
    ) -> int:
        """Append *rows* after the file's last row; return how many were appended."""
        ...
