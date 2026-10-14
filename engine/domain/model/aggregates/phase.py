"""Phase aggregate — owns effort computation. Scheduling is delegated.

Scheduling algorithms live in :mod:`engine.domain.services.roadmap_scheduler`
(Single Responsibility). Phase retains compute_effort and schedule_roadmap
as its public API, the latter delegating to the scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.entities.component import Component
from engine.domain.model.entities.executive_summary_data import ExecutiveSummaryData
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.entities.slide_note import SlideNote
from engine.domain.model.value_objects.group_effort import GroupEffort
from engine.domain.model.value_objects.phase_config import PhaseConfig
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_id import PhaseId
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap
from engine.domain.model.value_objects.resource_plan import ResourcePlan

__all__ = ["Phase"]


@dataclass
class Phase:
    """A delivery phase — the aggregate that owns its scheduling algorithm.

    The four roadmap views (resource, activity groups, build, lifecycle)
    are intrinsic to what a Phase *is*. The scheduling logic lives here,
    not in a service.
    """

    phase_id: PhaseId
    name: str
    description: str
    phase_name: str = ""            # column header in matrix ("Phase 1")
    integration_type: str = ""
    examples: str = ""
    build_activities: list[BuildActivity] = field(default_factory=list)
    project_activities: list[ProjectActivity] = field(default_factory=list)
    resource_plan: ResourcePlan = field(default_factory=ResourcePlan)
    config: PhaseConfig = field(default_factory=PhaseConfig)
    components: list[Component] = field(default_factory=list)

    # The pitch copy of this phase's deck: slides/P<n>-executive-summary.tsv
    # and slides/P<n>-notes.tsv. A deck sells one phase, so the copy is the phase's.
    executive_summary: ExecutiveSummaryData | None = None
    slide_notes: list[SlideNote] = field(default_factory=list)

    # Raw resource rows for quoter/financial generators (preserves Profile, Rate Day)
    resource_rows: list[dict[str, str]] = field(default_factory=list)

    # BRD index — set by the repository after requirements are loaded
    brd_order: list[str] = field(default_factory=list)
    req_to_category: dict[str, str] = field(default_factory=dict)


    def compute_effort(self) -> PhaseEffort:
        """Compute the effort breakdown for this phase.

        Groups the build activities, sums the project rows the build register
        does not already itemise, and carries the resource plan's capacity
        alongside as its own quantity. Build and overhead partition the
        authored effort, so they sum to it.
        """
        groups: dict[str, GroupEffort] = {}
        for act in self.build_activities:
            prev = groups.get(act.group, GroupEffort(count=0, effort=0.0))
            groups[act.group] = GroupEffort(
                count=prev.count + 1,
                effort=prev.effort + act.effort_md,
            )

        build_total = sum(g.effort for g in groups.values())

        overhead_rows: list[tuple[str, float]] = [
            (act.group, act.effort_md)
            for act in self.project_activities
            if not act.is_build_detailed
        ]
        overhead_total = sum(e for _, e in overhead_rows)

        return PhaseEffort(
            build_total=build_total,
            overhead_total=overhead_total,
            staffed_capacity=self.resource_plan.total_capacity,
            build_groups=groups,
            overhead_rows=overhead_rows,
        )

    def schedule_roadmap(self) -> PhaseRoadmap:
        """Run the full 4-view scheduling algorithm for this phase."""
        from engine.domain.services.roadmap_scheduler import schedule

        return schedule(self)

    def get_build_window(self) -> tuple[int, int] | None:
        """Convenience: detect build window from project activities."""
        from engine.domain.services.roadmap_scheduler import get_build_window

        return get_build_window(self)

    @property
    def has_executive_summary(self) -> bool:
        """Whether this phase carries a non-empty executive summary to open its deck with."""
        es = self.executive_summary
        return es is not None and bool(
            es.context_description or es.context_bullets or es.rationale or es.highlights
        )

    def get_slide_note(self, slide: str, position: str) -> str | None:
        """Look up this phase's slide note by slide name and position.

        Returns None if no note is defined for that slot.
        """
        for note in self.slide_notes:
            if note.slide == slide and note.position == position:
                return note.text
        return None
