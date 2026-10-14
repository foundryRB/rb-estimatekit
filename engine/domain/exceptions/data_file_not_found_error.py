"""An expected data file is missing from the project."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class DataFileNotFoundError(AppError):
    """An expected data file is missing from the project."""

    def __init__(self, path: Path, *, hint: str = "") -> None:
        self.path = path
        self.hint = hint
        msg = f"Required data file not found: {path}"
        if hint:
            msg += f" ({hint})"
        super().__init__(msg)
