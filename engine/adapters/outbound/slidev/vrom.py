"""Slide renderer: VROM cost summary.

Generates a single slide (12-vrom-summary.md) showing revenue per phase,
percentage breakdown, and a summary table.
"""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS, phase_colors_css
from engine.domain.constants.files.outputs import out_quoter_xlsx
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

from .vrom_revenue import (
    compute_phase_revenue,
    default_gm_pct,
    read_gm_label,
    read_quoter_revenue,
)

# ── Constants ───────────────────────────────────────────────────────────

_PHASE_CSS: dict[str, str] = {
    "Demo": "cf-phase--demo",
    "P1": "cf-phase--p1",
    "P2": "cf-phase--p2",
    "P3": "cf-phase--p3",
}
# Cyclic fallback for unknown / extra phases, indexed by phase position so
# each gets a distinct accent (mirrors effort.py's index-based cycle).
_CSS_CYCLE: list[str] = list(_PHASE_CSS.values())


# ── Helpers ─────────────────────────────────────────────────────────────

def _phase_style(pid: str, index: int, primary: str = DEFAULT_PRIMARY_CSS) -> tuple[str, str]:
    """Return (accent_color, css_class) for a phase.

    Known phases keep their mapped colour/class; unknown phases (e.g. ``P2A``,
    ``P2B``) cycle by position rather than collapsing to a single grey.
    """
    colors = phase_colors_css(primary)
    cycle = list(colors.values())
    color = colors.get(pid) or cycle[index % len(cycle)]
    css = _PHASE_CSS.get(pid) or _CSS_CYCLE[index % len(_CSS_CYCLE)]
    return color, css


def _fmt_eur(value: float) -> str:
    """Format *value* as ``€ 1,234,567`` (no decimals)."""
    raw = f"{value:,.0f}"  # e.g. "1,234,567"
    return f"€ {raw}"


# ── Slide renderer ──────────────────────────────────────────────────────

def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate VROM summary slide. Returns list of written filenames."""
    if not project.phases:
        return []

    excel_dir = output_dir.parent / "excel"
    from_excel = False

    # ── Collect per-phase revenue ───────────────────────────────────
    phase_revenues: dict[str, float] = {}
    for phase in project.phases:
        pid = phase.phase_id
        # 1) Try Excel
        rev = read_quoter_revenue(excel_dir, out_quoter_xlsx(pid))
        if rev is not None and rev > 0:
            phase_revenues[pid] = rev
            from_excel = True
        else:
            # 2) Fallback: compute from domain
            phase_revenues[pid] = compute_phase_revenue(phase)

    total_revenue = sum(phase_revenues.values())
    if total_revenue == 0:
        return []

    gm_label = (
        read_gm_label(excel_dir, [p.phase_id for p in project.phases])
        if from_excel else f"{default_gm_pct():.0%}"
    )
    source_note = "Quoter workbooks" if from_excel else "Domain model (computed)"

    # ── Build phase cards HTML ──────────────────────────────────────
    n_phases = len(project.phases)
    cards_html = ""
    for idx, phase in enumerate(project.phases):
        pid = phase.phase_id
        rev = phase_revenues.get(pid, 0.0)
        pct = round(rev / total_revenue * 100) if total_revenue else 0
        color, css = _phase_style(pid, idx, project.config.branding.primary_color)
        cards_html += (
            f'<div class="cf-card {css}" '
            f'style="border-top:3px solid {color};padding:0.5rem;text-align:center;">\n'
            f'  <div style="font-size:0.65rem;color:#888;">{pid}</div>\n'
            f'  <div style="font-weight:700;font-size:0.75rem;">{phase.name}</div>\n'
            f'  <div style="font-size:1.1rem;font-weight:700;color:{color};">'
            f'{_fmt_eur(rev)}</div>\n'
            f'  <div style="font-size:0.65rem;color:#666;">{pct}%</div>\n'
            f'</div>\n'
        )

    # ── Summary table ───────────────────────────────────────────────
    table_rows = ""
    for idx, phase in enumerate(project.phases):
        pid = phase.phase_id
        rev = phase_revenues.get(pid, 0.0)
        pct = round(rev / total_revenue * 100) if total_revenue else 0
        color, _ = _phase_style(pid, idx, project.config.branding.primary_color)
        table_rows += (
            f'| <span style="color:{color};font-weight:700;">●</span> {pid} '
            f'| {phase.name} '
            f'| {_fmt_eur(rev)} '
            f'| {pct}% |\n'
        )

    # ── Footer ──────────────────────────────────────────────────────
    foot = footer(project.config.name, project.config.branding.company)

    # ── Compose slide ───────────────────────────────────────────────
    grid_style = (
        f"display:grid;grid-template-columns:repeat({n_phases},1fr);gap:0.5rem;"
        f"margin-bottom:0.75rem;max-width:{n_phases * 200}px;"
        "margin-left:auto;margin-right:auto;"
    )
    content = f"""---
layout: default
---

# VROM — Cost Summary

<div class="cf-divider"></div>

<div style="{grid_style}">
{cards_html}
</div>

<div style="text-align:center;margin:0.5rem 0;">
  <span style="font-size:0.65rem;color:#888;">Total Revenue</span><br/>
  <span style="font-size:1.4rem;font-weight:700;">{_fmt_eur(total_revenue)}</span>
</div>

<div class="text-xs" style="margin-top:0.5rem;">

| Phase | Description | Revenue | % |
|---|---|---|---|
{table_rows}| | **TOTAL** | **{_fmt_eur(total_revenue)}** | **100%** |

</div>

<div class="cf-note mt-1">

GM {gm_label} · Source: {source_note}

</div>
{foot}{speaker_notes(phase, "vrom")}
"""

    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    fname = "12-vrom-summary.md"
    (pages_dir / fname).write_text(content, encoding="utf-8")
    return [fname]
