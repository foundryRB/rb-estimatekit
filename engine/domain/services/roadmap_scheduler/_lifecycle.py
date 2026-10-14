"""View 4 — Lifecycle: design/test overlay around the build window."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from engine.domain.constants.scheduling import DAYS_PER_MONTH
from engine.domain.model.value_objects.roadmap_view import RoadmapView
from engine.domain.model.value_objects.view_row import ViewRow

from ._helpers import _MARKER_MAP, first_true, last_true, order_categories

if TYPE_CHECKING:
    from engine.domain.model.value_objects.phase_config import PhaseConfig


def compute_lifecycle(
    build_active: dict[str, list[bool]],
    n_months: int,
    config: PhaseConfig,
    *,
    has_testing_effort: bool = False,
) -> dict[str, list[str]]:
    """Overlay design-lead and SIT/UAT windows around build milestones.

    When ``has_testing_effort`` is True but SIT+UAT = 0 (concurrent/integrated
    testing), the test milestone ▲ replaces the build milestone ◆ at each
    category's completion month — since acceptance is the deliverable that
    matters most in the feature lifecycle.
    """
    design_months = (
        math.ceil(config.design_lead_days / DAYS_PER_MONTH)
        if config.design_lead_days > 0 else 0
    )
    sit_m = (
        math.ceil(config.sit_days / DAYS_PER_MONTH)
        if config.sit_days > 0 else 0
    )
    uat_m = (
        math.ceil(config.uat_days / DAYS_PER_MONTH)
        if config.uat_days > 0 else 0
    )
    test_months = (
        math.ceil((config.sit_days + config.uat_days) / DAYS_PER_MONTH)
        if (config.sit_days + config.uat_days) > 0 else 0
    )
    if sit_m + uat_m > test_months and sit_m > 0:
        sit_m = test_months - uat_m

    max_end = n_months
    for flags in build_active.values():
        be = last_true(flags)
        if be is not None:
            max_end = max(max_end, be + 1 + test_months)

    result: dict[str, list[str]] = {}
    for cat, flags in build_active.items():
        cells = [""] * max_end
        bs, be = first_true(flags), last_true(flags)
        if bs is None or be is None:
            result[cat] = cells
            continue
        if design_months > 0:
            for m in range(max(0, bs - design_months), bs):
                cells[m] = "D"
        for m in range(bs, be + 1):
            cells[m] = "·"
        cells[be] = "◆"
        if test_months > 0:
            t_start, t_end = be + 1, be + 1 + test_months
            for m in range(t_start, min(t_end, max_end)):
                cells[m] = "T"
            t_ms = t_end - 1
            if 0 <= t_ms < max_end:
                cells[t_ms] = "▲"
        elif has_testing_effort:
            # Concurrent/integrated testing — test completes with build
            cells[be] = "▲"
        result[cat] = cells
    return result


def lifecycle_to_view(
    effort_by_cat: dict[str, float],
    lifecycle: dict[str, list[str]],
    base_labels: list[str],
    brd_order: list[str],
) -> RoadmapView:
    """Convert lifecycle raw data to a renderable view."""
    ordered = order_categories({c: [True] for c in lifecycle}, brd_order)
    max_len = max((len(c) for c in lifecycle.values()), default=len(base_labels))
    labels = list(base_labels)
    for i in range(len(labels), max_len):
        labels.append(f"M{i + 1}")
    rows: list[ViewRow] = []
    for cat in ordered:
        raw = lifecycle.get(cat, [])
        cells = [
            _MARKER_MAP.get(raw[i] if i < len(raw) else "", _MARKER_MAP[""])
            for i in range(len(labels))
        ]
        rows.append(ViewRow(label=cat, effort=round(effort_by_cat.get(cat, 0)), cells=cells))
    return RoadmapView(month_labels=labels, rows=rows)
