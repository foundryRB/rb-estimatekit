"""BuildActivity — a build activity contributing effort to the phase."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.requirement_id import RequirementId

__all__ = ["BuildActivity"]


@dataclass
class BuildActivity:
    """A build activity contributing effort to the phase."""

    activity_id: str
    group: str                      # "SIM Management", "Connectivity"
    name: str                       # "Implement SIM provisioning API"
    effort_md: float                # Effort in man-days
    req_ids: set[RequirementId] = field(default_factory=set)

    @property
    def is_traced(self) -> bool:
        """Whether this activity is linked to at least one requirement."""
        return bool(self.req_ids)
