"""A phase id names no phase the project defines."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class PhaseNotFoundError(AppError):
    """A phase id names no phase the project's phase table defines."""

    def __init__(self, phase_id: str, defined: list[str]) -> None:
        self.phase_id = phase_id
        self.defined = defined
        listed = ", ".join(defined) if defined else "no phases"
        super().__init__(f"Phase not found: {phase_id!r} (the project defines {listed})")
