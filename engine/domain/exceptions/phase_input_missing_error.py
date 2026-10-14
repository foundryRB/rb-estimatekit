"""A phase lacks an input its deck needs."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class PhaseInputMissingError(AppError):
    """The phase being sold has no content in an input its deck renders."""

    def __init__(self, phase_id: str, relative_path: str) -> None:
        self.phase_id = phase_id
        self.relative_path = relative_path
        super().__init__(
            f"Phase {phase_id} has no {relative_path}: author it before generating its deck"
        )
