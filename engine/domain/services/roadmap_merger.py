"""Merge per-phase roadmaps into an all-phases PhaseRoadmap.

Produces a proper PhaseRoadmap with RoadmapView objects containing real
CellMarker cells, suitable for both TSV writers and slide renderers.
"""

from __future__ import annotations

from collections import defaultdict

from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap
from engine.domain.model.value_objects.roadmap_view import RoadmapView
from engine.domain.model.value_objects.view_row import ViewRow

__all__ = ["merge_roadmaps"]

# Lifecycle raw cell markers → CellMarker mapping
_LIFECYCLE_MAP: dict[str, CellMarker] = {
    "D": CellMarker.DESIGN,
    "·": CellMarker.ACTIVE,
    "◆": CellMarker.MILESTONE,
    "T": CellMarker.TEST_ACTIVE,
    "▲": CellMarker.TEST_MILESTONE,
}


def merge_roadmaps(roadmaps: list[PhaseRoadmap]) -> PhaseRoadmap:
    """Merge per-phase roadmaps into a single all-phases PhaseRoadmap.

    Returns a PhaseRoadmap with ``phase_id="All"`` containing merged
    month labels (prefixed by phase ID) and concatenated views.
    """
    if not roadmaps:
        return PhaseRoadmap(phase_id="All")

    # ── Merged month labels ─────────────────────────────────────────
    merged_labels: list[str] = []
    phase_offsets: dict[str, int] = {}
    for rm in roadmaps:
        phase_offsets[rm.phase_id] = len(merged_labels)
        merged_labels.extend(f"{rm.phase_id}-{lbl}" for lbl in rm.month_labels)
    total_months = len(merged_labels)

    # ── Merge activity_groups view ──────────────────────────────────
    ag_rows: list[ViewRow] = []
    for rm in roadmaps:
        offset = phase_offsets[rm.phase_id]
        for row in rm.activity_groups.rows:
            # Prefix label with phase ID for the all-phases view
            label = f"{rm.phase_id}: {row.label}"
            # Extend cells to total_months with proper offset
            cells = [CellMarker.EMPTY] * total_months
            for i, marker in enumerate(row.cells):
                if offset + i < total_months:
                    cells[offset + i] = marker
            ag_rows.append(ViewRow(label=label, effort=row.effort, cells=cells))

    merged_ag = RoadmapView(month_labels=merged_labels, rows=ag_rows)

    # ── Merge lifecycle view ────────────────────────────────────────
    # Categories may appear in multiple phases — merge under same row.
    # First pass to discover the lifecycle extent (may overflow base months)
    lc_total = total_months
    for rm in roadmaps:
        offset = phase_offsets[rm.phase_id]
        for _cat, cells in rm.lifecycle_raw.items():
            lc_total = max(lc_total, offset + len(cells))

    # Pad labels if lifecycle overflows
    lc_labels = list(merged_labels)
    for i in range(len(lc_labels), lc_total):
        lc_labels.append(f"X-M{i + 1}")

    cat_order: list[str] = []
    cat_effort: dict[str, float] = defaultdict(float)
    cat_cells: dict[str, list[CellMarker]] = {}

    for rm in roadmaps:
        offset = phase_offsets[rm.phase_id]
        # Accumulate effort
        for cat, eff in rm.effort_by_cat.items():
            cat_effort[cat] += eff
            if cat not in cat_cells:
                cat_order.append(cat)
                cat_cells[cat] = [CellMarker.EMPTY] * lc_total

        # Merge lifecycle raw markers → CellMarker
        for cat, raw_cells in rm.lifecycle_raw.items():
            if cat not in cat_cells:
                cat_order.append(cat)
                cat_cells[cat] = [CellMarker.EMPTY] * lc_total
            for i, val in enumerate(raw_cells):
                if val and offset + i < lc_total:
                    marker = _LIFECYCLE_MAP.get(val, CellMarker.EMPTY)
                    if marker is not CellMarker.EMPTY:
                        cat_cells[cat][offset + i] = marker

    lc_rows = [
        ViewRow(label=cat, effort=cat_effort.get(cat, 0.0), cells=cat_cells[cat])
        for cat in cat_order
    ]
    merged_lc = RoadmapView(month_labels=lc_labels, rows=lc_rows)

    # ── Merge resource view (for resource table display) ────────────
    merged_streams: dict[str, list[float]] = {}
    for rm in roadmaps:
        for stream, caps in rm.stream_capacities.items():
            if stream not in merged_streams:
                merged_streams[stream] = [0.0] * total_months
            offset = phase_offsets[rm.phase_id]
            for i, cap in enumerate(caps):
                if offset + i < total_months:
                    merged_streams[stream][offset + i] = cap

    resource_rows = [
        ViewRow(
            label=stream,
            effort=sum(caps),
            cells=[CellMarker.EMPTY] * total_months,
            raw_values=caps,
        )
        for stream, caps in merged_streams.items()
    ]
    merged_resource = RoadmapView(month_labels=merged_labels, rows=resource_rows)

    # ── Merge raw fields (for TSV writer compatibility) ─────────────
    merged_effort_by_cat = dict(cat_effort)
    merged_build_active: dict[str, list[bool]] = {
        c: [False] * total_months for c in cat_order
    }
    merged_lifecycle_raw: dict[str, list[str]] = {
        c: [""] * lc_total for c in cat_order
    }

    for rm in roadmaps:
        offset = phase_offsets[rm.phase_id]
        for cat, flags in rm.build_active.items():
            if cat not in merged_build_active:
                merged_build_active[cat] = [False] * total_months
            for i, f in enumerate(flags):
                if f and offset + i < total_months:
                    merged_build_active[cat][offset + i] = True
        for cat, cells in rm.lifecycle_raw.items():
            if cat not in merged_lifecycle_raw:
                merged_lifecycle_raw[cat] = [""] * lc_total
            for i, val in enumerate(cells):
                if val and offset + i < lc_total:
                    merged_lifecycle_raw[cat][offset + i] = val

    return PhaseRoadmap(
        phase_id="All",
        month_labels=merged_labels,
        resource=merged_resource,
        activity_groups=merged_ag,
        build=RoadmapView(month_labels=merged_labels, rows=[]),
        lifecycle=merged_lc,
        stream_capacities=merged_streams,
        groups_raw=[],
        effort_by_cat=merged_effort_by_cat,
        build_active=merged_build_active,
        lifecycle_raw=merged_lifecycle_raw,
    )
