"""View 2 — Activity Groups: sequential scheduling within streams."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.group_schedule import GroupSchedule
from engine.domain.model.value_objects.roadmap_view import RoadmapView
from engine.domain.model.value_objects.view_row import ViewRow

if TYPE_CHECKING:
    from engine.domain.model.entities.project_activity import ProjectActivity
    from engine.domain.model.value_objects.resource_plan import ResourcePlan


def schedule_activity_groups(
    project_activities: list[ProjectActivity],
    plan: ResourcePlan,
    n_months: int,
) -> list[GroupSchedule]:
    """Schedule project-activity groups sequentially within each stream."""
    if not project_activities or n_months == 0:
        return []

    ordered = [
        (act.group, act.stream, act.effort_md)
        for act in project_activities if act.effort_md > 0
    ]
    stream_cum: dict[str, list[float]] = {}
    for _, stream, _ in ordered:
        if stream not in stream_cum:
            caps = plan.streams.get(stream, [0.0] * n_months)
            cum, total = [], 0.0
            for c in caps:
                total += c
                cum.append(total)
            stream_cum[stream] = cum

    consumed: dict[str, float] = {}
    results: list[GroupSchedule] = []
    for name, stream, effort in ordered:
        before = consumed.get(stream, 0.0)
        cum = stream_cum.get(stream, [])
        if not cum:
            continue
        start = next((m for m in range(n_months) if cum[m] > before + 0.001), 0)
        target = before + effort
        end = start
        for m in range(start, n_months):
            end = m
            if cum[m] >= target - 0.001:
                break
        consumed[stream] = before + effort
        results.append(GroupSchedule(
            name=name, stream=stream, effort=effort,
            start_month=start, end_month=end,
        ))
    return results


def find_build_window(groups: list[GroupSchedule]) -> tuple[int, int] | None:
    """Detect the build window from scheduled activity groups."""
    for g in groups:
        if g.name.lower().startswith("build activit"):
            return (g.start_month, g.end_month)
    return None


def groups_to_view(groups: list[GroupSchedule], labels: list[str]) -> RoadmapView:
    """Convert scheduled groups to a renderable view."""
    n = len(labels)
    rows: list[ViewRow] = []
    for g in groups:
        cells = []
        for m in range(n):
            if m == g.end_month:
                cells.append(CellMarker.MILESTONE)
            elif g.start_month <= m < g.end_month:
                cells.append(CellMarker.ACTIVE)
            else:
                cells.append(CellMarker.EMPTY)
        rows.append(ViewRow(label=g.name, effort=g.effort, cells=cells, stream=g.stream))
    return RoadmapView(month_labels=labels, rows=rows)
