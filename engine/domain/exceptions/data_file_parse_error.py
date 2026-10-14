"""A data file could not be parsed."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class DataFileParseError(AppError):
    """A data file could not be parsed (bad encoding, malformed rows, etc.)."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Parse error in {path.name}: {reason}")
