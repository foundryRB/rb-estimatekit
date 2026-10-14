"""A row write was refused: the rows do not fit the file's header, or no row matches."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class InvalidRowError(AppError):
    """A row write was refused: the rows do not fit the file's header, or no row matches."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}; nothing was written")
