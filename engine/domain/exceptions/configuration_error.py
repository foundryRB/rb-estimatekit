"""Project configuration is invalid or incomplete."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class ConfigurationError(AppError):
    """Project configuration is invalid or incomplete."""

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"Configuration error [{key}]: {reason}")
