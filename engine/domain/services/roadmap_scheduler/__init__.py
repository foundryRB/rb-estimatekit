"""Roadmap scheduling domain service.

Stateless functions implementing the four-view scheduling pipeline
for a Phase:

  1. **Resource** — monthly capacity per stream
  2. **Activity Groups** — sequential scheduling within streams
  3. **Build** — greedy spread + milestones by BRD category
  4. **Lifecycle** — design/test overlay around the build window
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

from ._activity_groups import (
    find_build_window,
    groups_to_view,
    schedule_activity_groups,
)
from ._build import build_to_view, compute_category_effort, schedule_build
from ._helpers import month_labels
from ._lifecycle import compute_lifecycle, lifecycle_to_view
from ._resource import schedule_resource

if TYPE_CHECKING:
    from engine.domain.model.aggregates.phase import Phase

__all__ = ["get_build_window", "schedule"]


def schedule(phase: Phase) -> PhaseRoadmap:
    """Run the full four-view scheduling pipeline for a single phase."""
    n_months = phase.resource_plan.n_months
    labels = month_labels(n_months)

    resource = schedule_resource(phase.resource_plan, labels)
    groups = schedule_activity_groups(
        phase.project_activities, phase.resource_plan, n_months,
    )
    activity_groups = groups_to_view(groups, labels)

    build_window = find_build_window(groups)
    effort_by_cat = compute_category_effort(
        phase.build_activities, phase.req_to_category, phase.brd_order,
    )
    build_active = schedule_build(
        effort_by_cat, build_window, n_months,
        phase.resource_plan, phase.brd_order, phase.phase_id,
    )
    build = build_to_view(effort_by_cat, build_active, labels, phase.brd_order)

    has_testing_effort = any(
        act.effort_md > 0
        for act in phase.project_activities
        if "testing" in act.group.lower() or "quality" in act.group.lower()
    )
    lifecycle_raw = compute_lifecycle(
        build_active, n_months, phase.config,
        has_testing_effort=has_testing_effort,
    )
    lifecycle = lifecycle_to_view(
        effort_by_cat, lifecycle_raw, labels, phase.brd_order,
    )

    return PhaseRoadmap(
        phase_id=phase.phase_id,
        month_labels=labels,
        resource=resource,
        activity_groups=activity_groups,
        build=build,
        lifecycle=lifecycle,
        stream_capacities=dict(phase.resource_plan.streams),
        groups_raw=groups,
        build_start=build_window[0] if build_window else 0,
        build_end=build_window[1] if build_window else n_months - 1,
        effort_by_cat=effort_by_cat,
        build_active=build_active,
        lifecycle_raw=lifecycle_raw,
        config=phase.config,
    )


def get_build_window(phase: Phase) -> tuple[int, int] | None:
    """Convenience: detect build window from project activities."""
    groups = schedule_activity_groups(
        phase.project_activities, phase.resource_plan,
        phase.resource_plan.n_months,
    )
    return find_build_window(groups)
