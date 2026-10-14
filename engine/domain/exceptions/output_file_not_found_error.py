"""A requested output file does not exist or is outside the output directory."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class OutputFileNotFoundError(AppError):
    """A requested output file does not exist or is outside the output directory."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Output file not found: {path}")
