"""Failed to load project data from disk."""

from __future__ import annotations

from pathlib import Path

from engine.domain.exceptions.app_error import AppError


class ProjectLoadError(AppError):
    """Failed to load project data from disk."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load project at {path}: {reason}")
