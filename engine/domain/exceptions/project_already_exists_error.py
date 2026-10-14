"""A project directory already exists at the specified path."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class ProjectAlreadyExistsError(AppError):
    """A project directory already exists at the specified path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Project already exists: {path}")
