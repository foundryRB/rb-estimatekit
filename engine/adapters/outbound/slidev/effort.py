"""Slide renderer: effort estimate breakdown."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.constants.colors import DEFAULT_PRIMARY_CSS, phase_colors_css
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.man_days import format_md
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

# Phase CSS classes; the accent colours are the brand palette (P1 carries the
# project's primary colour). Falls back cyclically for unknown phases.
_PHASE_CSS: dict[str, str] = {
    "Demo": "rb-phase--demo",
    "P1": "rb-phase--p1",
    "P2": "rb-phase--p2",
    "P3": "rb-phase--p3",
}
_CSS_CYCLE: list[str] = list(_PHASE_CSS.values())


def _phase_css(phase_id: str, index: int, primary: str = DEFAULT_PRIMARY_CSS) -> tuple[str, str]:
    """Return (css_class, accent_color) for a phase, ``primary`` being the brand one."""
    colors = phase_colors_css(primary)
    cycle = list(colors.values())
    css = _PHASE_CSS.get(phase_id) or _CSS_CYCLE[index % len(_CSS_CYCLE)]
    color = colors.get(phase_id) or cycle[index % len(cycle)]
    return css, color


# ── Slide: Effort Estimate (all-phases summary) ────────────────────────


def _render_effort_estimate(
    project: Project,
    efforts: dict[str, PhaseEffort],
    output_dir: Path,
    *,
    footer_note: str | None = None,
    notes: str = "",
) -> str | None:
    """Generate 09-effort-estimate.md, the all-phases summary. Returns filename or None.

    *footer_note* and *notes* are the sold phase's ``effort`` footer note and
    speaker notes; the table itself covers every phase.
    """
    if not project.phases or not efforts:
        return None

    req_counts = project.count_requirements_per_phase()
    total_reqs = len(project.requirements)

    # Phase cards
    cards = ""
    for idx, phase in enumerate(project.phases):
        pid = phase.phase_id
        eff = efforts.get(pid)
        if eff is None:
            continue
        css_class, color = _phase_css(pid, idx, project.config.branding.primary_color)
        activity_count = sum(g.count for g in eff.build_groups.values())
        cards += (
            f'  <div class="rb-phase {css_class}" style="padding:0.6rem;">\n'
            f'    <div class="text-xs font-bold">{pid} — {phase.name}</div>\n'
            f'    <div style="font-size:1.4rem;font-weight:700;color:{color};">'
            f"{format_md(eff.authored_total)} MD</div>\n"
            f'    <div class="text-xs">{req_counts.get(pid, 0)} reqs · '
            f"{activity_count} activities</div>\n"
            f'    <div class="text-xs">{format_md(eff.build_total)} Build + '
            f"{format_md(eff.overhead_total)} Overhead</div>\n"
            f'    <div class="text-xs opacity-70">'
            f"{format_md(eff.staffed_capacity)} MD staffed</div>\n"
            f"  </div>\n"
        )

    # Summary table
    tbl = ""
    for phase in project.phases:
        pid = phase.phase_id
        eff = efforts.get(pid)
        if eff is None:
            continue
        tbl += (
            f"| **{pid}** | {req_counts.get(pid, 0)} | "
            f"{format_md(eff.build_total)} | {format_md(eff.overhead_total)} | "
            f"**{format_md(eff.authored_total)}** | {format_md(eff.staffed_capacity)} |\n"
        )

    total_build = sum(e.build_total for e in efforts.values())
    total_overhead = sum(e.overhead_total for e in efforts.values())
    total_effort = sum(e.authored_total for e in efforts.values())
    total_staffed = sum(e.staffed_capacity for e in efforts.values())

    tbl += (
        f"| **TOTAL** | **{total_reqs}** | "
        f"**{format_md(total_build)}** | **{format_md(total_overhead)}** | "
        f"**{format_md(total_effort)}** | **{format_md(total_staffed)}** |"
    )

    n_cols = len(project.phases)

    # Footer note from the sold phase's notes (never hard-coded)
    note_text = footer_note
    note_block = ""
    if note_text:
        note_block = f"""
<div class="rb-note mt-1">

{note_text}

</div>
"""

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Effort Estimate

<div class="rb-divider"></div>

<div class="grid grid-cols-{n_cols} gap-3 mt-2 text-center">
{cards}</div>

<div class="text-xs mt-2">

| Phase | Reqs | Build (MD) | Overhead (MD) | Effort (MD) | Staffed (MD) |
|---|:---:|---:|---:|---:|---:|
{tbl}

</div>

<div class="text-xs mt-1 opacity-70">

Effort is the authored estimate: Build + Overhead. Staffed is the capacity the
resource plan books to deliver it, which covers the effort rather than equalling it.

</div>
{note_block}
{foot}{notes}
"""

    filename = "09-effort-estimate.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


# ── Slides: Per-Phase Effort Breakdown ──────────────────────────────────


def _render_phase_breakdown(
    phase_id: str,
    phase_name: str,
    effort: PhaseEffort,
    output_dir: Path,
    foot: str,
    *,
    phase_index: int = 0,
    notes: str = "",
) -> str | None:
    """Generate per-phase effort breakdown. Returns filename or None."""
    if not effort.build_groups and not effort.overhead_rows:
        return None

    # Build activities table — sorted by effort descending
    b_rows = ""
    sorted_groups = sorted(
        effort.build_groups.items(), key=lambda kv: kv[1].effort, reverse=True
    )
    for group_name, g in sorted_groups:
        pct = round(g.effort / effort.build_total * 100) if effort.build_total else 0
        b_rows += (
            f"| **{group_name}** | {g.count} | {format_md(g.effort)} MD | {pct}% |\n"
        )
    total_activities = sum(g.count for g in effort.build_groups.values())
    b_rows += (
        f"| **TOTAL** | **{total_activities}** | "
        f"**{format_md(effort.build_total)} MD** | **100%** |"
    )

    # Overhead table
    p_rows = ""
    for name, eff_md in effort.overhead_rows:
        p_rows += f"| {name} | {format_md(eff_md)} MD |\n"
    p_rows += f"| **TOTAL** | **{format_md(effort.overhead_total)} MD** |"

    content = f"""---
layout: default
---

# {phase_id} — Effort Breakdown

<div class="rb-divider"></div>

<div class="grid grid-cols-2 gap-8 mt-3">

<div>

### Build Activities — {format_md(effort.build_total)} MD

<div class="text-xs mt-2">

| Area | Activities | Effort | % |
|---|:---:|---:|:---:|
{b_rows}

</div>

</div>

<div>

### Project Overhead — {format_md(effort.overhead_total)} MD

<div class="text-xs mt-2">

| Activity Group | Effort |
|---|---:|
{p_rows}

</div>

</div>

</div>

<div class="rb-summary mt-3">
<strong>Total {phase_id}:</strong> <strong>{format_md(effort.authored_total)} MD</strong> effort
= {format_md(effort.build_total)} MD Build + {format_md(effort.overhead_total)} MD Overhead
&middot; {format_md(effort.staffed_capacity)} MD staffed capacity
</div>
{foot}{notes}
"""

    filename = f"11-{phase_index:02d}a-effort-{phase_id.lower()}.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


# ── Public entry point ──────────────────────────────────────────────────


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate the all-phases effort summary and the sold phase's breakdown.

    Returns filenames. The summary keeps every phase as context; the
    breakdown is the sold phase's alone.
    """
    written: list[str] = []
    notes = speaker_notes(phase, "effort")

    # Slide 1: all-phases summary
    fname = _render_effort_estimate(
        project,
        efforts,
        output_dir,
        footer_note=phase.get_slide_note("effort", "footer-note"),
        notes=notes,
    )
    if fname:
        written.append(fname)

    # Slide 2: the sold phase's breakdown, numbered by its place in the phase table
    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)
    eff = efforts.get(phase.phase_id)
    if eff is not None:
        position = next(
            (i for i, p in enumerate(project.phases) if p.phase_id == phase.phase_id), 0,
        )
        fname = _render_phase_breakdown(
            phase.phase_id,
            phase.name,
            eff,
            output_dir,
            foot,
            phase_index=position + 1,
            notes=notes,
        )
        if fname:
            written.append(fname)

    return written
