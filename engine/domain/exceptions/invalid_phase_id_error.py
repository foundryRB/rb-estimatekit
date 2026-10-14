"""A phase id does not follow the P<n> convention that names phase files."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class InvalidPhaseIdError(AppError):
    """The phase id is not of the form ``P<n>``."""

    def __init__(self, phase_id: str) -> None:
        self.phase_id = phase_id
        super().__init__(f"Invalid phase id: {phase_id!r} (expected P<n>, such as P3)")
