"""Shared rendering helpers for Slidev markdown generation.

HTML builders for Gantt charts, effort tables, requirement matrices, etc.
These are format-specific (Slidev HTML-in-markdown) and belong in the adapter.
"""

from __future__ import annotations

from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.value_objects.group_effort import GroupEffort


def render_gantt_row(label: str, cells: list[str], css_class: str = "") -> str:
    """Render a single Gantt chart row as an HTML table row.

    *cells* is a list of HTML cell contents (may include styled <span> elements).
    """
    label_td = f'<td class="gantt-label {css_class}">{label}</td>'
    cell_tds = "".join(f"<td>{c}</td>" for c in cells)
    return f"<tr>{label_td}{cell_tds}</tr>"


def render_effort_table(groups: dict[str, GroupEffort], total: float) -> str:
    """Render an effort breakdown as an HTML table.

    Returns a complete ``<table>`` element with group rows and a total row.
    """
    rows = ""
    for name, g in groups.items():
        pct = round(g.effort / total * 100) if total else 0
        rows += (
            f"<tr>"
            f'<td style="text-align:left;">{name}</td>'
            f'<td style="text-align:center;">{g.count}</td>'
            f'<td style="text-align:right;">{round(g.effort)} MD</td>'
            f'<td style="text-align:right;">{pct}%</td>'
            f"</tr>\n"
        )
    rows += (
        '<tr style="border-top:2px solid #333;font-weight:700;">'
        '<td style="text-align:left;">TOTAL</td>'
        f'<td style="text-align:center;">{sum(g.count for g in groups.values())}</td>'
        f'<td style="text-align:right;">{round(total)} MD</td>'
        '<td style="text-align:right;">100%</td>'
        "</tr>"
    )
    return (
        '<table style="width:100%;border-collapse:collapse;font-size:0.65rem;">\n'
        "<thead><tr>"
        '<th style="text-align:left;">Build Group</th>'
        '<th style="text-align:center;">Activities</th>'
        '<th style="text-align:right;">Effort</th>'
        '<th style="text-align:right;">%</th>'
        "</tr></thead>\n"
        f"<tbody>\n{rows}</tbody>\n</table>"
    )


def footer(project_name: str, company: str) -> str:
    """Return the standard Slavic footer HTML."""
    brand = company.split("\u2014")[0].strip() if "\u2014" in company else company
    suffix = company.split("\u2014")[1].strip() if "\u2014" in company else ""
    return (
        '\n<div class="rb-footer">\n'
        f'  <span><span class="rb-brand">{brand}'
        f'</span> \u2014 {suffix}</span>\n'
        f"  <span>{project_name}</span>\n"
        "</div>"
    )


def speaker_notes(phase: Phase, slide_id: str) -> str:
    """Return a Slidev speaker-notes comment block from *phase*'s notes, or empty string.

    The deck sells one phase, so the notes spoken over any slide are that
    phase's ``speaker`` note for *slide_id*. If found, the text is wrapped in
    an HTML comment that Slidev renders only in Presenter Mode.
    """
    text = phase.get_slide_note(slide_id, "speaker")
    if not text:
        return ""
    return f"\n\n<!--\n{text}\n-->"
