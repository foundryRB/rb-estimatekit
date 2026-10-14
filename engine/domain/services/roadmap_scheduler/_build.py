"""View 3 — Build: greedy spread + milestones by BRD category."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import TYPE_CHECKING

from engine.domain.constants.scheduling import DEV_STREAM_PREFIX
from engine.domain.exceptions.scheduling_error import SchedulingError
from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.roadmap_view import RoadmapView
from engine.domain.model.value_objects.view_row import ViewRow

from ._helpers import last_true, order_categories

if TYPE_CHECKING:
    from engine.domain.model.entities.build_activity import BuildActivity
    from engine.domain.model.value_objects.phase_id import PhaseId
    from engine.domain.model.value_objects.resource_plan import ResourcePlan


def compute_category_effort(
    build_activities: list[BuildActivity],
    req_to_cat: dict[str, str],
    brd_order: list[str],
) -> dict[str, float]:
    """Aggregate build effort by BRD category."""
    effort_by_cat: dict[str, float] = defaultdict(float)
    unique_cats = list(dict.fromkeys(req_to_cat.values()))
    for act in build_activities:
        raw_ids = {str(rid) for rid in act.req_ids}
        if not raw_ids:
            continue
        if raw_ids == {"ALL"}:
            if unique_cats:
                share = act.effort_md / len(unique_cats)
                for c in unique_cats:
                    effort_by_cat[c] += share
            continue
        cat_counts: dict[str, int] = defaultdict(int)
        for rid in raw_ids:
            cat_counts[req_to_cat.get(rid, "Unmatched")] += 1
        total = len(raw_ids)
        for c, count in cat_counts.items():
            effort_by_cat[c] += act.effort_md * count / total
    return dict(effort_by_cat)


def _build_capacity(plan: ResourcePlan, n: int) -> list[float]:
    """Sum monthly capacity available to build activities.

    Streams named with the DEV_STREAM_PREFIX convention carry the build
    capacity when any stream uses it; a plan with plain stream names
    contributes all of its streams.
    """
    dev_streams = [s for s in plan.streams if s.startswith(DEV_STREAM_PREFIX)]
    selected = dev_streams or list(plan.streams)
    result = [0.0] * n
    for stream in selected:
        for i, c in enumerate(plan.streams[stream]):
            if i < n:
                result[i] += c
    return result


def _schedule_order(effort_by_cat: dict[str, float], brd_order: list[str]) -> list[str]:
    """Determine build scheduling order: first BRD-priority category, then by size."""
    ordered: list[str] = []
    for cat in brd_order:
        if cat in effort_by_cat:
            ordered.append(cat)
            break
    ordered.extend(sorted(
        (c for c in effort_by_cat if c not in ordered),
        key=lambda c: -effort_by_cat[c],
    ))
    return ordered


def schedule_build(
    effort_by_cat: dict[str, float],
    build_window: tuple[int, int] | None,
    n_months: int,
    plan: ResourcePlan,
    brd_order: list[str],
    phase_id: PhaseId,
) -> dict[str, list[bool]]:
    """Greedy-spread build activities across the build window.

    Raises SchedulingError when there is build effort to place but the
    build window holds no capacity.
    """
    if not effort_by_cat or n_months == 0:
        return {cat: [False] * max(n_months, 1) for cat in effort_by_cat}

    build_start, build_end = build_window or (0, n_months - 1)
    if build_end < build_start:
        return {cat: [False] * n_months for cat in effort_by_cat}

    build_n = build_end - build_start + 1
    build_caps = _build_capacity(plan, n_months)
    window_caps = build_caps[build_start:build_end + 1]
    avg_cap = sum(window_caps) / build_n
    if avg_cap <= 0 and any(e > 0 for e in effort_by_cat.values()):
        raise SchedulingError(
            phase_id,
            f"no build capacity in months M{build_start + 1}-M{build_end + 1}; build "
            f"capacity comes from '{DEV_STREAM_PREFIX}*' streams when the numbered-stream "
            "naming convention is used, and from all streams otherwise",
        )

    ordered = _schedule_order(effort_by_cat, brd_order)
    active: dict[str, list[bool]] = {}
    milestone_count = [0] * build_n

    for cat in ordered:
        effort = effort_by_cat[cat]
        months_needed = (
            1 if effort <= 0
            else max(1, min(math.ceil(effort / avg_cap), build_n))
        )
        flags = [False] * n_months
        best_rel_end, best_mc = months_needed - 1, float("inf")
        for rel_end in range(months_needed - 1, build_n):
            mc = milestone_count[rel_end]
            if mc < best_mc:
                best_mc = mc
                best_rel_end = rel_end
        rel_start = best_rel_end - months_needed + 1
        for rel_m in range(rel_start, best_rel_end + 1):
            abs_m = build_start + rel_m
            if abs_m < n_months:
                flags[abs_m] = True
        milestone_count[best_rel_end] += 1
        active[cat] = flags
    return active


def build_to_view(
    effort_by_cat: dict[str, float],
    build_active: dict[str, list[bool]],
    labels: list[str],
    brd_order: list[str],
) -> RoadmapView:
    """Convert build-active flags to a renderable view."""
    ordered = order_categories(build_active, brd_order)
    n = len(labels)
    rows: list[ViewRow] = []
    for cat in ordered:
        flags = build_active.get(cat, [False] * n)
        last = last_true(flags)
        cells = [
            CellMarker.MILESTONE if (i < len(flags) and flags[i] and i == last)
            else CellMarker.ACTIVE if (i < len(flags) and flags[i])
            else CellMarker.EMPTY
            for i in range(n)
        ]
        rows.append(ViewRow(label=cat, effort=round(effort_by_cat.get(cat, 0)), cells=cells))
    return RoadmapView(month_labels=labels, rows=rows)
