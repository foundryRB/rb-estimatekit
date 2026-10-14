"""A file path escapes its project directory."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class InvalidPathError(AppError):
    """The provided relative path escapes the project directory."""

    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        super().__init__(f"Path escapes project directory: {relative_path}")
