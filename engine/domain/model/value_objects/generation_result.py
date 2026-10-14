"""GenerationResult — outcome of a generation run."""

from __future__ import annotations

from dataclasses import dataclass

from engine.domain.model.value_objects.phase_id import PhaseId
from engine.domain.model.value_objects.pipeline import Pipeline

__all__ = ["GenerationResult"]


@dataclass(frozen=True)
class GenerationResult:
    """Outcome of running one or more generation pipelines."""

    outcomes: dict[Pipeline, bool]
    """Maps each executed pipeline to its success status."""

    phase: PhaseId | None = None
    """The phase the slide deck was built for; None when the slides pipeline did not run."""

    @property
    def success(self) -> bool:
        """True when every pipeline succeeded."""
        return all(self.outcomes.values())
