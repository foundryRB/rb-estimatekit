"""Phase column detection and HTML header-row builder for Gantt charts."""

from __future__ import annotations

from engine.adapters.outbound.slidev.roadmap_slides.colors import phase_color
from engine.adapters.outbound.slidev.roadmap_slides.labels import detect_phase_from_label
from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS

__all__ = [
    "compute_col_phases",
    "compute_phase_groups",
    "phase_header_row",
]


def compute_col_phases(month_labels: list[str], phase_ids: list[str]) -> list[str]:
    """Map each month label to its phase id.

    Columns before the first detected phase fall back to the project's first
    phase id (never a hardcoded phase).
    """
    default = phase_ids[0] if phase_ids else ""
    result: list[str] = []
    last_phase = ""
    for lbl in month_labels:
        detected = detect_phase_from_label(lbl, phase_ids)
        if detected:
            last_phase = detected
        result.append(last_phase or default)
    return result


def compute_phase_groups(col_phases: list[str]) -> list[tuple[str, int]]:
    """Group consecutive columns by phase for a header row."""
    if not col_phases:
        return []
    groups: list[tuple[str, int]] = []
    current = col_phases[0]
    count = 0
    for cp in col_phases:
        if cp == current:
            count += 1
        else:
            groups.append((current, count))
            current = cp
            count = 1
    groups.append((current, count))
    return groups


def phase_header_row(col_phases: list[str], extra_cols: int = 0, primary: str = DEFAULT_PRIMARY_CSS) -> str:
    """Build the coloured phase-group ``<tr>`` for multi-phase views."""
    groups = compute_phase_groups(col_phases)
    html = '<tr class="rb-gantt-phase-row">\n'
    for _ in range(extra_cols):
        html += '  <th class="rb-gantt-label"></th>\n'
    for phase, span in groups:
        color = phase_color(phase, primary)
        html += (
            f'  <th colspan="{span}" class="rb-gantt-phase" '
            f'style="background:{color};color:#fff;">{phase}</th>\n'
        )
    html += "</tr>\n"
    return html
