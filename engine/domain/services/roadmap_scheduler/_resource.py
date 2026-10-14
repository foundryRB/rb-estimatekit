"""View 1 — Resource: monthly capacity per stream."""

from __future__ import annotations

from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.resource_plan import ResourcePlan
from engine.domain.model.value_objects.roadmap_view import RoadmapView
from engine.domain.model.value_objects.view_row import ViewRow


def schedule_resource(
    plan: ResourcePlan, month_labels: list[str],
) -> RoadmapView:
    """Build the resource-capacity view for a phase."""
    rows: list[ViewRow] = []
    for stream in sorted(plan.streams):
        caps = plan.streams[stream]
        cells = [CellMarker.EMPTY] * len(month_labels)
        rows.append(ViewRow(label=stream, effort=sum(caps), cells=cells, raw_values=caps))
    return RoadmapView(month_labels=month_labels, rows=rows)
