"""A project directory or its project.yaml could not be found."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class ProjectNotFoundError(AppError):
    """A project directory or its ``project.yaml`` could not be found."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Project not found: {path}")
