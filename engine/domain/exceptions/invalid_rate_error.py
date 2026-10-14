"""A resource 'Rate Day' value could not be parsed as a daily rate."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class InvalidRateError(AppError):
    """A resource 'Rate Day' value could not be parsed as a daily rate."""

    def __init__(self, value: str, context: str) -> None:
        self.value = value
        self.context = context
        super().__init__(f"Invalid Rate Day value {value!r} ({context})")
