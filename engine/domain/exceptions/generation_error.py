"""A generator or renderer failed to produce output."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class GenerationError(AppError):
    """A generator or renderer failed to produce output."""

    def __init__(self, generator: str, reason: str) -> None:
        self.generator = generator
        self.reason = reason
        super().__init__(f"Generation failed [{generator}]: {reason}")
