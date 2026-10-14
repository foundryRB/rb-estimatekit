"""Slide renderer: requirements overview and matrix."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

# CSS class per phase index (for category cards)
_CAT_CSS = ["cf-cat--demo", "cf-cat--p1", "cf-cat--p12", "cf-cat--p23"]
# Legend dot CSS classes (matching the above)
_LEGEND_CSS = [
    "cf-legend-dot--demo",
    "cf-legend-dot--p1",
    "cf-legend-dot--p12",
    "cf-legend-dot--p23",
]


def _join_legend(parts: list[str]) -> str:
    """Join legend items with spacing."""
    sep = " &nbsp;&nbsp;\n"
    return sep.join(parts)


def _phase_class(phase_counts: dict[str, int], phase_ids: list[str]) -> str:
    """Determine the CSS class for a category card based on dominant phase."""
    if not phase_ids:
        return _CAT_CSS[-1]
    # First phase with most allocations wins
    if phase_counts.get(phase_ids[0], 0) > 0:
        return _CAT_CSS[0]
    if len(phase_ids) >= 2 and phase_counts.get(phase_ids[1], 0) > sum(
        phase_counts.get(p, 0) for p in phase_ids[2:]
    ):
        return _CAT_CSS[1] if len(_CAT_CSS) > 1 else _CAT_CSS[-1]
    if len(phase_ids) >= 3 and phase_counts.get(phase_ids[2], 0) > 0:
        return _CAT_CSS[2] if len(_CAT_CSS) > 2 else _CAT_CSS[-1]
    return _CAT_CSS[-1]


def _count_per_category_per_phase(
    project: Project,
) -> tuple[
    OrderedDict[str, dict[str, int]],   # cat_name -> {phase_id -> count}
    list[Category],                      # categories in encounter order
    dict[str, int],                      # phase totals
]:
    """Build per-category, per-phase requirement counts from domain model."""
    categories = project.discover_categories()
    phase_ids = [p.phase_id for p in project.phases]

    cat_counts: OrderedDict[str, dict[str, int]] = OrderedDict()
    for cat in categories:
        cat_counts[cat.name] = {pid: 0 for pid in phase_ids}

    for req in project.requirements:
        cat_name = req.category.name
        if cat_name not in cat_counts:
            cat_counts[cat_name] = {pid: 0 for pid in phase_ids}
        for pid in phase_ids:
            if req.is_allocated_to(pid):
                cat_counts[cat_name][pid] += 1

    # Phase totals
    phase_totals: dict[str, int] = {pid: 0 for pid in phase_ids}
    for counts in cat_counts.values():
        for pid in phase_ids:
            phase_totals[pid] += counts.get(pid, 0)

    return cat_counts, categories, phase_totals


# ── Slide: Requirements Overview ────────────────────────────────────────


def _render_overview(project: Project, output_dir: Path, *, notes: str = "") -> str | None:
    """Generate 03-requirements-overview.md. Returns filename or None."""
    if not project.requirements:
        return None

    cat_counts, categories, phase_totals = _count_per_category_per_phase(project)
    phase_ids = [p.phase_id for p in project.phases]
    total = len(project.requirements)

    # Build category lookup for display_name
    cat_lookup: dict[str, Category] = {c.name: c for c in categories}

    # Build category cards
    cards = ""
    for cat_name, counts in cat_counts.items():
        cat_obj = cat_lookup.get(cat_name)
        display = cat_obj.display_name if cat_obj else cat_name
        cat_total = sum(counts.values())
        css = _phase_class(counts, phase_ids)
        cards += (
            f'\n<div class="{css} cf-cat">\n'
            f'  <div class="cf-cat-name">{display}</div>\n'
            f'  <div class="cf-cat-count">{cat_total}</div>\n'
            f"</div>"
        )

    # Build legend
    legend_parts: list[str] = []
    for i, phase in enumerate(project.phases):
        cls = _LEGEND_CSS[i] if i < len(_LEGEND_CSS) else _LEGEND_CSS[-1]
        legend_parts.append(
            f'<span class="{cls}">■</span> {phase.phase_id}'
            f" ({phase_totals.get(phase.phase_id, 0)} reqs)"
        )

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Requirements Overview

<div class="cf-divider"></div>

**{total} requirements** extracted from customer needs, organized by functional area.

<div class="grid grid-cols-4 gap-3 mt-3">
{cards}
</div>

<div class="mt-4 cf-legend">
{_join_legend(legend_parts)}
</div>
{foot}{notes}
"""

    filename = "03-requirements-overview.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


# ── Slide: Requirements × Phase Matrix ──────────────────────────────────


def _render_matrix(project: Project, output_dir: Path, *, notes: str = "") -> str | None:
    """Generate 04-requirements-matrix.md. Returns filename or None."""
    if not project.requirements:
        return None

    cat_counts, categories, phase_totals = _count_per_category_per_phase(project)
    phase_ids = [p.phase_id for p in project.phases]
    total = len(project.requirements)

    cat_lookup: dict[str, Category] = {c.name: c for c in categories}

    # Header cells
    header_cells = "".join(
        f'<th style="text-align:center;min-width:3rem;">{pid}</th>'
        for pid in phase_ids
    )

    # Body rows
    html_rows = ""
    for cat_name, counts in cat_counts.items():
        cat_obj = cat_lookup.get(cat_name)
        display = cat_obj.display_name if cat_obj else cat_name
        cat_total = sum(counts.values())
        cells = ""
        for pid in phase_ids:
            v = counts.get(pid, 0)
            if v > 0:
                cells += f'<td style="text-align:center;font-weight:600;">{v}</td>'
            else:
                cells += '<td style="text-align:center;color:#ccc;">—</td>'
        html_rows += (
            f"<tr><td><strong>{display}</strong></td>"
            f"{cells}"
            f"<td style='text-align:center;'>{cat_total}</td></tr>\n"
        )

    # Total row
    total_cells = "".join(
        f'<td style="text-align:center;font-weight:700;">'
        f"{phase_totals.get(pid, 0)}</td>"
        for pid in phase_ids
    )
    html_rows += (
        "<tr style='border-top:2px solid #333;'>"
        "<td><strong>TOTAL</strong></td>"
        f"{total_cells}"
        f"<td style='text-align:center;font-weight:700;'>{total}</td></tr>"
    )

    # Phase legend
    phase_descs = " &nbsp;|&nbsp; ".join(
        f"**{p.phase_id}** = {p.name}" for p in project.phases
    )

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Requirements × Phase Matrix

<div class="cf-divider"></div>

**{total} requirements** across {len(project.phases)} phases.

<div style="font-size:0.7rem;margin-top:0.5rem;">
<table style="width:100%;border-collapse:collapse;">
<thead>
<tr style="background:#f5f5f5;">
  <th style="text-align:left;min-width:8rem;">Category</th>
  {header_cells}
  <th style="text-align:center;">Total</th>
</tr>
</thead>
<tbody>
{html_rows}
</tbody>
</table>
</div>

<div class="mt-2" style="font-size:0.6rem;color:var(--cf-mid-grey);">

{phase_descs}

</div>
{foot}{notes}
"""

    filename = "04-requirements-matrix.md"
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
    """Generate requirements overview + matrix slides. Returns filenames."""
    written: list[str] = []
    notes = speaker_notes(phase, "requirements")
    for gen in (_render_overview, _render_matrix):
        fname = gen(project, output_dir, notes=notes)
        if fname:
            written.append(fname)
    return written
