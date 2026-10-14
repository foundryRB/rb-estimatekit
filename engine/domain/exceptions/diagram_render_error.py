"""A diagram source failed to render."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class DiagramRenderError(AppError):
    """A diagram source failed to render."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Diagram rendering failed: {reason}")
