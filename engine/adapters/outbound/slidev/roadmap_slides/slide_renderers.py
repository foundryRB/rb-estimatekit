"""Slide renderers for per-phase and all-phases roadmap Gantt charts."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.roadmap_slides.colors import phase_color
from engine.adapters.outbound.slidev.roadmap_slides.gantt_builders import (
    build_activity_group_gantt,
    build_lifecycle_gantt,
)
from engine.adapters.outbound.slidev.roadmap_slides.resource_table import (
    build_resource_table,
)
from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS
from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap
from engine.domain.model.value_objects.roadmap_view import RoadmapView

__all__ = [
    "render_activity_group_all_slide",
    "render_activity_group_slide",
    "render_lifecycle_all_slide",
    "render_lifecycle_slide",
]


def _fit_zoom(view: RoadmapView, *, compact: bool = False) -> str:
    """Return a CSS zoom property string to fit the gantt in the slide viewport.

    Returns an empty string when no scaling is needed (zoom >= 1).
    Slidev renders at a fixed resolution (~960×540).  Available content
    area after title/divider/legend is approximately 920×400 px.
    """
    n_rows = len(view.rows)
    n_months = view.n_months
    # Approximate pixel dimensions
    row_h = 16 if compact else 22
    col_w = 24 if compact else 30
    fixed_w = 140 if compact else 220  # label + stream + effort cols
    header_h = 50 if not compact else 38

    table_h = header_h + n_rows * row_h
    table_w = fixed_w + n_months * col_w

    avail_h, avail_w = 400, 920
    zoom_y = avail_h / table_h if table_h > avail_h else 1.0
    zoom_w = avail_w / table_w if table_w > avail_w else 1.0
    zoom = min(zoom_y, zoom_w)

    if zoom < 0.98:
        return f"zoom:{zoom:.2f};"
    return ""


def _count_milestones(view: RoadmapView) -> int:
    """Count MILESTONE markers (◆) across all rows in a view."""
    return sum(
        1 for row in view.rows for c in row.cells if c is CellMarker.MILESTONE
    )


def _has_marker(view: RoadmapView, marker: CellMarker) -> bool:
    """Check whether any cell in *view* contains *marker*."""
    return any(c is marker for row in view.rows for c in row.cells)


def render_activity_group_slide(
    roadmap: PhaseRoadmap,
    foot: str,
    output_dir: Path,
    *,
    phase_ids: list[str],
    phase_index: int = 0,
    primary: str = DEFAULT_PRIMARY_CSS,
    notes: str = "",
) -> str | None:
    """Generate per-phase activity group slide. Returns filename or None."""
    view = roadmap.activity_groups
    if not view.rows:
        return None

    pid = roadmap.phase_id
    color = phase_color(pid, primary)
    n_milestones = _count_milestones(view)
    n_groups = len(view.rows)

    gantt_html = build_activity_group_gantt(view, phase_ids=phase_ids, single_phase=pid, primary=primary)
    resource_html = build_resource_table(roadmap.resource, pid, primary=primary)
    zoom = _fit_zoom(view)
    zoom_style = f" {zoom}" if zoom else ""

    content = f"""\
---
layout: default
---

# {pid} — Delivery Roadmap

<div class="cf-divider"></div>

<div class="text-xs mt-1" style="font-size:0.62rem;{zoom_style}">

{gantt_html}

</div>

{resource_html}

<div class="cf-legend mt-1" style="font-size:0.6rem;">
<span class="cf-gantt-legend-active" style="background:{color};"></span> Active &nbsp;&nbsp;
<span class="cf-gantt-legend-milestone">◆</span> Milestone &nbsp;&nbsp;
<strong>{n_groups} activity groups · {n_milestones} milestones</strong>
</div>
{foot}{notes}
"""

    filename = f"11-{phase_index:02d}b-roadmap-{pid.lower()}.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


def render_activity_group_all_slide(
    roadmap: PhaseRoadmap,
    n_phases: int,
    foot: str,
    output_dir: Path,
    *,
    phase_ids: list[str],
    notes: str = "",
    primary: str = DEFAULT_PRIMARY_CSS,
) -> str | None:
    """Generate ``11-roadmap-all.md``. Returns filename or None."""
    view = roadmap.activity_groups
    if not view.rows:
        return None

    gantt_html = build_activity_group_gantt(view, phase_ids=phase_ids, compact=True, primary=primary)
    n_milestones = _count_milestones(view)
    zoom = _fit_zoom(view, compact=True)
    zoom_style = f" {zoom}" if zoom else ""

    content = f"""\
---
layout: default
---

# All Phases — Delivery Roadmap

<div class="cf-divider"></div>

<div class="text-xs mt-1" style="overflow-x:auto;font-size:0.55rem;{zoom_style}">

{gantt_html}

</div>

<div class="cf-legend mt-1" style="font-size:0.55rem;">
<span class="cf-gantt-legend-active" style="background:{DEFAULT_PRIMARY_CSS};"></span> Active &nbsp;
<span class="cf-gantt-legend-milestone">◆</span> Milestone &nbsp;&nbsp;
<strong>{n_milestones} milestones across {n_phases} phases</strong>
</div>
{foot}{notes}
"""

    filename = "10a-roadmap-all.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


def render_lifecycle_slide(
    roadmap: PhaseRoadmap,
    foot: str,
    output_dir: Path,
    *,
    phase_ids: list[str],
    phase_index: int = 0,
    primary: str = DEFAULT_PRIMARY_CSS,
    notes: str = "",
) -> str | None:
    """Generate per-phase lifecycle slide. Returns filename or None."""
    view = roadmap.lifecycle
    if not view.rows:
        return None

    pid = roadmap.phase_id
    color = phase_color(pid, primary)
    n_milestones = _count_milestones(view)

    has_design = _has_marker(view, CellMarker.DESIGN)
    has_testing = _has_marker(view, CellMarker.TEST_ACTIVE) or _has_marker(
        view, CellMarker.TEST_MILESTONE
    )

    gantt_html = build_lifecycle_gantt(view, phase_ids=phase_ids, single_phase=pid, primary=primary)

    # Build adaptive legend
    design_legend = (
        '\n<span class="cf-gantt-legend-design" style="background:#1976D2;"></span>'
        " Design &nbsp;&nbsp;"
    ) if has_design else ""
    test_legend = (
        '\n<span class="cf-gantt-legend-test" style="background:#2E7D32;"></span>'
        " Testing &nbsp;&nbsp;"
        '\n<span class="cf-gantt-legend-test-milestone">▲</span>'
        " Test Complete &nbsp;&nbsp;"
    ) if has_testing else ""

    zoom = _fit_zoom(view)
    zoom_style = f" style=\"{zoom}\"" if zoom else ""

    content = f"""\
---
layout: default
---

# {pid} — Feature Lifecycle

<div class="cf-divider"></div>

<div class="text-xs mt-2"{zoom_style}>

{gantt_html}

</div>

<div class="cf-legend mt-2 text-xs">{design_legend}
<span class="cf-gantt-legend-active" style="background:{color};"></span> Build &nbsp;&nbsp;
<span class="cf-gantt-legend-milestone">◆</span> Complete &nbsp;&nbsp;{test_legend}
<strong>{n_milestones} milestones</strong>
</div>
{foot}{notes}
"""

    filename = f"11-{phase_index:02d}c-lifecycle-{pid.lower()}.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


def render_lifecycle_all_slide(
    roadmap: PhaseRoadmap,
    n_phases: int,
    foot: str,
    output_dir: Path,
    *,
    phase_ids: list[str],
    notes: str = "",
    primary: str = DEFAULT_PRIMARY_CSS,
) -> str | None:
    """Generate ``11-roadmap-all-lifecycle.md``. Returns filename or None."""
    view = roadmap.lifecycle
    if not view.rows:
        return None

    gantt_html = build_lifecycle_gantt(view, phase_ids=phase_ids, compact=True, primary=primary)
    n_milestones = _count_milestones(view)
    zoom = _fit_zoom(view, compact=True)
    zoom_style = f" {zoom}" if zoom else ""

    content = f"""\
---
layout: default
---

# All Phases — Feature Lifecycle

<div class="cf-divider"></div>

<div class="text-xs mt-1" style="overflow-x:auto;font-size:0.62rem;{zoom_style}">

{gantt_html}

</div>

<div class="cf-legend mt-1" style="font-size:0.6rem;">
<span class="cf-gantt-legend-design" style="background:#1976D2;"></span> Design &nbsp;
<span class="cf-gantt-legend-active" style="background:{DEFAULT_PRIMARY_CSS};"></span> Build &nbsp;
<span class="cf-gantt-legend-milestone">◆</span> Complete &nbsp;
<span class="cf-gantt-legend-test" style="background:#2E7D32;"></span> Testing &nbsp;
<span class="cf-gantt-legend-test-milestone">▲</span> Test Complete &nbsp;&nbsp;
<strong>{n_milestones} milestones across {n_phases} phases</strong>
</div>
{foot}{notes}
"""

    filename = "10b-lifecycle-all.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename
