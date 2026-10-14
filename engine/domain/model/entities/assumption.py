"""Assumption — a project assumption with risk classification."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.confidence import Confidence
from engine.domain.model.value_objects.impact import Impact
from engine.domain.model.value_objects.requirement_id import RequirementId

__all__ = ["Assumption"]


@dataclass
class Assumption:
    """A project assumption with risk classification."""

    assumption_id: str
    group: str
    assumption: str
    short_title: str
    confidence: Confidence
    impact: Impact
    req_ids: set[RequirementId] = field(default_factory=set)

    @property
    def is_high_risk(self) -> bool:
        """Whether this assumption is high-risk (low confidence + high/critical impact)."""
        return (
            self.confidence == Confidence.LOW
            and self.impact in (Impact.CRITICAL, Impact.HIGH)
        )
