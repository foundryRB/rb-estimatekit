"""The scheduling algorithm encountered an unrecoverable state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.domain.exceptions.app_error import AppError

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_id import PhaseId


class SchedulingError(AppError):
    """The scheduling algorithm encountered an unrecoverable state."""

    def __init__(self, phase_id: PhaseId, reason: str) -> None:
        self.phase_id = phase_id
        self.reason = reason
        super().__init__(f"Scheduling error in phase {phase_id}: {reason}")
