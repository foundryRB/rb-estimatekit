"""PhaseRoadmap — complete roadmap for a single phase."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from engine.domain.model.value_objects.roadmap_view import RoadmapView

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_config import PhaseConfig
    from engine.domain.model.value_objects.phase_id import PhaseId

__all__ = ["PhaseRoadmap"]


@dataclass(frozen=True)
class PhaseRoadmap:
    """Complete roadmap for a single phase — all four views."""

    phase_id: PhaseId
    month_labels: list[str] = field(default_factory=list)
    resource: RoadmapView = field(default_factory=RoadmapView)
    activity_groups: RoadmapView = field(default_factory=RoadmapView)
    build: RoadmapView = field(default_factory=RoadmapView)
    lifecycle: RoadmapView = field(default_factory=RoadmapView)

    # Raw intermediate data — needed by merger and TSV writer
    stream_capacities: dict[str, list[float]] = field(default_factory=dict)
    groups_raw: list[Any] = field(default_factory=list)
    build_start: int = 0
    build_end: int = 0
    effort_by_cat: dict[str, float] = field(default_factory=dict)
    build_active: dict[str, list[bool]] = field(default_factory=dict)
    lifecycle_raw: dict[str, list[str]] = field(default_factory=dict)
    config: PhaseConfig | None = None
