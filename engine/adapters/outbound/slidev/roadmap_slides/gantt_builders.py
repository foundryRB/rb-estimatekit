"""HTML table builders for Activity Group and Feature Lifecycle Gantt charts."""

from __future__ import annotations

from engine.adapters.outbound.slidev.roadmap_slides.colors import (
    DESIGN_COLOR,
    TEST_COLOR,
    phase_color,
)
from engine.adapters.outbound.slidev.roadmap_slides.labels import (
    strip_month_prefix,
    strip_row_phase_prefix,
)
from engine.adapters.outbound.slidev.roadmap_slides.phase_headers import (
    compute_col_phases,
    phase_header_row,
)
from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS
from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.man_days import format_md
from engine.domain.model.value_objects.roadmap_view import RoadmapView

__all__ = [
    "build_activity_group_gantt",
    "build_lifecycle_gantt",
]


def build_activity_group_gantt(
    view: RoadmapView,
    *,
    phase_ids: list[str],
    single_phase: str | None = None,
    compact: bool = False,
    primary: str = DEFAULT_PRIMARY_CSS,
) -> str:
    """Build Activity Group Gantt HTML table.

    Columns: Activity Group | Stream | MD | month cells
    In *compact* mode (all-phases), Stream and MD columns are hidden.
    *phase_ids* is the project's actual phase-id set, used to parse labels.
    """
    labels = view.month_labels
    n_months = view.n_months
    col_phases = (
        [single_phase] * n_months if single_phase
        else compute_col_phases(labels, phase_ids)
    )
    display_labels = [strip_month_prefix(lbl, phase_ids) for lbl in labels]
    is_multi_phase = single_phase is None

    show_detail = not compact
    extra_cols = 3 if show_detail else 1

    tbl_cls = "cf-gantt cf-gantt-compact" if compact else "cf-gantt"
    tbl_style = ' style="line-height:1.0;"' if compact else ""
    html = f'<div class="cf-gantt-wrap">\n<table class="{tbl_cls}"{tbl_style}>\n<thead>\n'

    # Phase group header (all-phases only)
    if is_multi_phase:
        html += phase_header_row(col_phases, extra_cols=extra_cols, primary=primary)

    # Column headers
    html += '<tr class="cf-gantt-header">\n'
    html += '  <th class="cf-gantt-label">Activity Group</th>\n'
    if show_detail:
        html += '  <th class="cf-gantt-stream">Stream</th>\n'
        html += '  <th class="cf-gantt-effort">MD</th>\n'
    for lbl in display_labels:
        html += f'  <th class="cf-gantt-month">{lbl}</th>\n'
    html += "</tr>\n</thead>\n<tbody>\n"

    # Data rows
    for row in view.rows:
        display_label = (
            strip_row_phase_prefix(row.label, phase_ids) if is_multi_phase
            else row.label
        )

        html += "<tr>\n"
        html += f'  <td class="cf-gantt-label">{display_label}</td>\n'
        if show_detail:
            html += f'  <td class="cf-gantt-stream">{row.stream}</td>\n'
            html += f'  <td class="cf-gantt-effort">{format_md(row.effort)}</td>\n'

        for i in range(n_months):
            marker = row.cells[i] if i < len(row.cells) else CellMarker.EMPTY
            color = (
                phase_color(single_phase, primary) if single_phase
                else phase_color(col_phases[i], primary)
            )

            if marker is CellMarker.MILESTONE:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-milestone" '
                    f'style="background:{color};">◆</td>\n'
                )
            elif marker is CellMarker.ACTIVE:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-active" '
                    f'style="background:{color};"></td>\n'
                )
            else:
                html += '  <td class="cf-gantt-cell"></td>\n'

        html += "</tr>\n"

    html += "</tbody>\n</table>\n</div>"
    return html


def build_lifecycle_gantt(
    view: RoadmapView,
    *,
    phase_ids: list[str],
    single_phase: str | None = None,
    compact: bool = False,
    primary: str = DEFAULT_PRIMARY_CSS,
) -> str:
    """Build Feature Lifecycle Gantt HTML table (D/·/◆/T/▲).

    *phase_ids* is the project's actual phase-id set, used to parse labels.
    """
    labels = view.month_labels
    n_months = view.n_months
    col_phases = (
        [single_phase] * n_months if single_phase
        else compute_col_phases(labels, phase_ids)
    )
    display_labels = [strip_month_prefix(lbl, phase_ids) for lbl in labels]
    is_multi_phase = single_phase is None

    tbl_cls = "cf-gantt cf-gantt-compact" if compact else "cf-gantt"
    tbl_style = ' style="line-height:1.0;"' if compact else ""
    html = f'<div class="cf-gantt-wrap">\n<table class="{tbl_cls}"{tbl_style}>\n<thead>\n'

    # Phase group header (all-phases only)
    if is_multi_phase:
        html += phase_header_row(col_phases, extra_cols=2, primary=primary)

    html += '<tr class="cf-gantt-header">\n'
    html += '  <th class="cf-gantt-label">Category</th>\n'
    html += '  <th class="cf-gantt-effort">MD</th>\n'
    for lbl in display_labels:
        html += f'  <th class="cf-gantt-month">{lbl}</th>\n'
    html += "</tr>\n</thead>\n<tbody>\n"

    for row in view.rows:
        html += "<tr>\n"
        html += f'  <td class="cf-gantt-label">{row.label}</td>\n'
        html += f'  <td class="cf-gantt-effort">{format_md(row.effort)}</td>\n'

        for i in range(n_months):
            marker = row.cells[i] if i < len(row.cells) else CellMarker.EMPTY
            build_color = (
                phase_color(single_phase, primary) if single_phase
                else phase_color(col_phases[i], primary)
            )

            if marker is CellMarker.MILESTONE:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-milestone" '
                    f'style="background:{build_color};">◆</td>\n'
                )
            elif marker is CellMarker.ACTIVE:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-active" '
                    f'style="background:{build_color};"></td>\n'
                )
            elif marker is CellMarker.DESIGN:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-design" '
                    f'style="background:{DESIGN_COLOR};"></td>\n'
                )
            elif marker is CellMarker.TEST_MILESTONE:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-test-milestone" '
                    f'style="background:{TEST_COLOR};">▲</td>\n'
                )
            elif marker is CellMarker.TEST_ACTIVE:
                html += (
                    f'  <td class="cf-gantt-cell cf-gantt-test-active" '
                    f'style="background:{TEST_COLOR};"></td>\n'
                )
            else:
                html += '  <td class="cf-gantt-cell"></td>\n'

        html += "</tr>\n"

    html += "</tbody>\n</table>\n</div>"
    return html
