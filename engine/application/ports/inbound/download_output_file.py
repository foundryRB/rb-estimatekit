"""Inbound port: download a single generated output file."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["DownloadOutputFilePort"]


@runtime_checkable
class DownloadOutputFilePort(Protocol):
    """Resolve and validate an output file for download."""

    def execute(self, project_path: Path, relative_path: str) -> Path:
        """Return the resolved absolute path to the output file."""
        ...
