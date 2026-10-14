"""TSV mergers for all-phases roadmap views."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from engine.adapters.outbound.roadmap.view_writers import (
    write_activity_groups,
    write_build,
    write_lifecycle,
    write_resource,
)
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

__all__ = [
    "merge_activity_groups",
    "merge_build",
    "merge_lifecycle",
    "merge_resource",
]


def merge_resource(out_dir: Path, roadmaps: list[PhaseRoadmap]) -> None:
    """Merge resource views across phases and write as All."""
    merged_labels: list[str] = []
    merged_streams: dict[str, list[float]] = {}
    for rm in roadmaps:
        merged_labels.extend(f"{rm.phase_id}-{lbl}" for lbl in rm.month_labels)
        for stream, caps in rm.stream_capacities.items():
            if stream not in merged_streams:
                merged_streams[stream] = []
            while len(merged_streams[stream]) < len(merged_labels) - len(rm.month_labels):
                merged_streams[stream].append(0.0)
            merged_streams[stream].extend(caps)
    n = len(merged_labels)
    for s in merged_streams:
        while len(merged_streams[s]) < n:
            merged_streams[s].append(0.0)
    write_resource(out_dir, "All", merged_streams, merged_labels)


def merge_activity_groups(out_dir: Path, roadmaps: list[PhaseRoadmap]) -> None:
    """Merge activity group views across phases and write as All."""
    from engine.domain.model.value_objects.group_schedule import GroupSchedule
    merged_labels: list[str] = []
    merged_groups: list[GroupSchedule] = []
    offset = 0
    for rm in roadmaps:
        merged_labels.extend(f"{rm.phase_id}-{lbl}" for lbl in rm.month_labels)
        for g in rm.groups_raw:
            merged_groups.append(GroupSchedule(
                name=f"{rm.phase_id}: {g.name}", stream=g.stream, effort=g.effort,
                start_month=g.start_month + offset, end_month=g.end_month + offset,
            ))
        offset += len(rm.month_labels)
    write_activity_groups(out_dir, "All", merged_groups, merged_labels)


def merge_build(out_dir: Path, roadmaps: list[PhaseRoadmap]) -> None:
    """Merge build views across phases and write as All."""
    merged_labels: list[str] = []
    all_cats: list[str] = []
    for rm in roadmaps:
        for cat in rm.build_active:
            if cat not in all_cats:
                all_cats.append(cat)
    total_months = sum(len(rm.month_labels) for rm in roadmaps)
    merged_effort: dict[str, float] = defaultdict(float)
    merged_active: dict[str, list[bool]] = {c: [False] * total_months for c in all_cats}
    offset = 0
    for rm in roadmaps:
        merged_labels.extend(f"{rm.phase_id}-{lbl}" for lbl in rm.month_labels)
        for cat, eff in rm.effort_by_cat.items():
            merged_effort[cat] += eff
        for cat, flags in rm.build_active.items():
            for i, f in enumerate(flags):
                if f:
                    merged_active[cat][offset + i] = True
        offset += len(rm.month_labels)

    # Build a fake PhaseRoadmap for the writer
    from engine.domain.model.value_objects.view_row import ViewRow
    fake = PhaseRoadmap(
        phase_id="All", month_labels=merged_labels,
        effort_by_cat=dict(merged_effort), build_active=merged_active,
        build=type(rm.build)(
            month_labels=merged_labels,
            rows=[ViewRow(label=c, effort=0, cells=[]) for c in all_cats],
        ),
        lifecycle_raw={},
    )
    write_build(out_dir, "All", fake)


def merge_lifecycle(out_dir: Path, roadmaps: list[PhaseRoadmap]) -> None:
    """Merge lifecycle views across phases and write as All."""
    merged_labels: list[str] = []
    all_cats: list[str] = []
    for rm in roadmaps:
        for cat in rm.lifecycle_raw:
            if cat not in all_cats:
                all_cats.append(cat)

    total_base = sum(len(rm.month_labels) for rm in roadmaps)
    total_months = total_base
    offset = 0
    for rm in roadmaps:
        for _cat, cells in rm.lifecycle_raw.items():
            total_months = max(total_months, offset + len(cells))
        offset += len(rm.month_labels)

    offset = 0
    for rm in roadmaps:
        merged_labels.extend(f"{rm.phase_id}-{lbl}" for lbl in rm.month_labels)
        offset += len(rm.month_labels)
    for i in range(len(merged_labels), total_months):
        merged_labels.append(f"X-M{i + 1}")

    merged_effort: dict[str, float] = defaultdict(float)
    merged_lifecycle: dict[str, list[str]] = {c: [""] * total_months for c in all_cats}
    merged_active: dict[str, list[bool]] = {c: [False] * total_months for c in all_cats}

    offset = 0
    for rm in roadmaps:
        for cat, eff in rm.effort_by_cat.items():
            merged_effort[cat] += eff
        for cat, cells in rm.lifecycle_raw.items():
            for i, val in enumerate(cells):
                ai = offset + i
                if ai < total_months and val:
                    merged_lifecycle[cat][ai] = val
        for cat, flags in rm.build_active.items():
            for i, f in enumerate(flags):
                if f:
                    merged_active[cat][offset + i] = True
        offset += len(rm.month_labels)

    from engine.domain.model.value_objects.view_row import ViewRow
    fake = PhaseRoadmap(
        phase_id="All", month_labels=merged_labels,
        effort_by_cat=dict(merged_effort),
        build_active=merged_active,
        lifecycle_raw=merged_lifecycle,
        lifecycle=type(rm.lifecycle)(
            month_labels=merged_labels,
            rows=[ViewRow(label=c, effort=0, cells=[]) for c in all_cats],
        ),
        build=type(rm.build)(
            month_labels=merged_labels,
            rows=[ViewRow(label=c, effort=0, cells=[]) for c in all_cats],
        ),
    )
    write_lifecycle(out_dir, "All", fake)
