"""RoadmapView — one of the four roadmap views."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.view_row import ViewRow

__all__ = ["RoadmapView"]


@dataclass(frozen=True)
class RoadmapView:
    """One of the four roadmap views (resource, activities, build, lifecycle)."""

    month_labels: list[str] = field(default_factory=list)
    rows: list[ViewRow] = field(default_factory=list)

    @property
    def n_months(self) -> int:
        """Number of months in this view."""
        return len(self.month_labels)
