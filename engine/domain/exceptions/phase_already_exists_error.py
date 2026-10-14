"""A phase's files already exist in the project."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class PhaseAlreadyExistsError(AppError):
    """The project already carries files for the phase being minted."""

    def __init__(self, phase_id: str, files: list[str]) -> None:
        self.phase_id = phase_id
        self.files = files
        super().__init__(
            f"Phase {phase_id} already has files: {', '.join(files)} "
            "(pass force to overwrite them with the example set)"
        )
