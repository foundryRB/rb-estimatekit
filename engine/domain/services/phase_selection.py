"""Select the phase a deck is built for."""

from __future__ import annotations

from engine.domain.constants.files.inputs import SLIDES_EXECUTIVE_SUMMARY, slides_path
from engine.domain.exceptions import (
    PhaseInputMissingError,
    PhaseNotFoundError,
    PhaseRequiredError,
)
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project

__all__ = ["select_phase", "select_phase_with_pitch"]


def select_phase(project: Project, phase_id: str | None) -> Phase:
    """Return the phase *phase_id* names, or the project's only phase when none is named.

    A deck sells one phase, so a project with several phases needs the phase named.
    """
    defined = [p.phase_id for p in project.phases]
    if phase_id is None:
        if len(project.phases) == 1:
            return project.phases[0]
        raise PhaseRequiredError(defined)
    phase = project.get_phase(phase_id)
    if phase is None:
        raise PhaseNotFoundError(phase_id, defined)
    return phase


def select_phase_with_pitch(project: Project, phase_id: str | None) -> Phase:
    """Like :func:`select_phase`, and the phase carries the pitch its deck opens with.

    A deck cannot be built for a phase without its executive summary, so the
    refusal comes here, before any pipeline has written.
    """
    phase = select_phase(project, phase_id)
    if not phase.has_executive_summary:
        raise PhaseInputMissingError(
            phase.phase_id, slides_path(phase.phase_id, SLIDES_EXECUTIVE_SUMMARY),
        )
    return phase
