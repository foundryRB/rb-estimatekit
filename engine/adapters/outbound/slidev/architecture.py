"""Slide renderer: architecture and guidelines."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.component import Component
from engine.domain.model.entities.guideline import Guideline
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap


def _group_components(components: list[Component]) -> OrderedDict[str, list[Component]]:
    """Group components by layer, preserving encounter order."""
    layers: OrderedDict[str, list[Component]] = OrderedDict()
    for c in components:
        layers.setdefault(c.layer, []).append(c)
    return layers


def _group_guidelines(guidelines: list[Guideline]) -> OrderedDict[str, list[Guideline]]:
    """Group guidelines by their .group attribute, preserving order."""
    groups: OrderedDict[str, list[Guideline]] = OrderedDict()
    for g in guidelines:
        groups.setdefault(g.group, []).append(g)
    return groups


def _render_guidelines_table(groups_subset: list[tuple[str, list[Guideline]]]) -> str:
    """Render guideline groups as markdown table rows."""
    rows = ""
    for group, items in groups_subset:
        for i, g in enumerate(items):
            # Truncate description to first sentence, max 90 chars
            desc = g.description
            short = desc.split(".")[0].strip() if "." in desc else desc
            if len(short) > 90:
                short = short[:87] + "…"
            group_cell = f"**{group}**" if i == 0 else ""
            rows += f"| {group_cell} | {g.guideline_id} | **{g.name}** | {short} |\n"
    return rows


# ── Slide 1: Architecture & Infrastructure ──────────────────────────────


def _render_architecture(project: Project, phase: Phase, output_dir: Path) -> str | None:
    """Generate 06-architecture.md for the phase being sold. Returns filename or None.

    The slide shows *phase*'s component inventory: a deck sells one phase, and
    on a multi-phase project every phase carries its own inventory.
    """
    if not phase.components:
        return None

    components = phase.components
    layers = _group_components(components)
    total = len(components)

    # Layer summary table
    layer_text = ""
    for layer, items in layers.items():
        techs: set[str] = set()
        for it in items:
            if it.technology:
                first_tech = it.technology.split("(")[0].split("+")[0].strip()
                if first_tech:
                    techs.add(first_tech)
        tech_str = ", ".join(sorted(techs)[:4])
        layer_text += f"| **{layer}** | {len(items)} | {tech_str} |\n"

    # Infrastructure components table
    infra = [c for c in components if c.layer == "Infrastructure"]
    infra_rows = ""
    for c in infra:
        infra_rows += f"| **{c.name}** | {c.technology} |\n"

    guidelines_count = len(project.guidelines_for(phase.phase_id))
    notes = speaker_notes(phase, "architecture")

    # Dynamic note from the phase's SlideNote data (no hard-coded text)
    note = phase.get_slide_note("architecture", "note") or ""
    note_block = ""
    if note:
        note_block = f"""
<div class="rb-note mt-1">

{note}

</div>
"""

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    comp_summary = (
        f"**{phase.phase_id} {phase.name}**: **{total} components** across {len(layers)} layers. "
        f"{guidelines_count} architecture guidelines govern its design decisions."
    )

    content = f"""---
layout: default
---

# Architecture & Infrastructure <span class="text-sm text-gray-400">{phase.phase_id}</span>

<div class="rb-divider"></div>

{comp_summary}

<div class="grid grid-cols-2 gap-6 mt-2 text-xs">

<div>

<div class="text-xs font-bold" style="margin-bottom:0.25rem;">Component Summary</div>

| Layer | # | Key Technologies |
|---|:---:|---|
{layer_text}

</div>

<div>

<div class="text-xs font-bold" style="margin-bottom:0.25rem;">Infrastructure</div>

| Component | Technology |
|---|---|
{infra_rows}
{note_block}
</div>

</div>
{foot}{notes}
"""

    filename = "06-architecture.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


# ── Slides 2–3: Architecture Guidelines ─────────────────────────────────


def _render_guidelines(project: Project, phase: Phase, output_dir: Path) -> list[str]:
    """Generate guideline slides for the phase being sold. Returns filenames.

    Renders the guidelines governing *phase*: the platform's (``All``) and the
    phase's own, never another phase's decisions.
    Uses a single page when ≤ 8 total guidelines or ≤ 3 groups.
    Splits across two pages only when there are many guidelines.
    """
    guidelines = project.guidelines_for(phase.phase_id)
    if not guidelines:
        return []

    groups = _group_guidelines(guidelines)
    group_list = list(groups.items())
    n_groups = len(group_list)
    guidelines_count = len(guidelines)
    areas_count = n_groups

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)
    notes = speaker_notes(phase, "architecture")

    filenames: list[str] = []
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    guide_summary = (
        f"**{guidelines_count} guidelines** across {areas_count} areas"
        " \u2014 governing decisions for scope, integration and delivery."
    )

    # Single page when there are few guidelines (≤8) or few groups (≤3)
    needs_split = guidelines_count > 8 and n_groups > 3

    if not needs_split:
        # Single page — all guidelines
        rows = _render_guidelines_table(group_list)
        group_names = ", ".join(g for g, _ in group_list)

        content = f"""---
layout: default
---

# Architecture Guidelines

<div class="rb-divider"></div>

{guide_summary}

<div class="text-xs">

| Area | ID | Guideline | Description |
|---|---|---|---|
{rows}

</div>

<div class="rb-note mt-1">

{group_names}

</div>
{foot}{notes}
"""
        fname = "06-guidelines-1.md"
        (pages_dir / fname).write_text(content, encoding="utf-8")
        filenames.append(fname)
    else:
        # Split: first 3 groups on slide 1, remaining on slide 2
        mid = 3
        slide1_groups = group_list[:mid]
        slide2_groups = group_list[mid:]

        # Slide 1
        slide1_rows = _render_guidelines_table(slide1_groups)
        slide1_group_names = ", ".join(g for g, _ in slide1_groups)

        content_1 = f"""---
layout: default
---

# Architecture Guidelines <span class="text-sm text-gray-400">(1/2)</span>

<div class="rb-divider"></div>

{guide_summary}

<div class="text-xs">

| Area | ID | Guideline | Description |
|---|---|---|---|
{slide1_rows}

</div>

<div class="rb-note mt-1">

{slide1_group_names}

</div>
{foot}{notes}
"""
        fname1 = "06-guidelines-1.md"
        (pages_dir / fname1).write_text(content_1, encoding="utf-8")
        filenames.append(fname1)

        # Slide 2
        slide2_rows = _render_guidelines_table(slide2_groups)
        slide2_group_names = ", ".join(g for g, _ in slide2_groups)

        content_2 = f"""---
layout: default
---

# Architecture Guidelines <span class="text-sm text-gray-400">(2/2)</span>

<div class="rb-divider"></div>

<div class="text-xs">

| Area | ID | Guideline | Description |
|---|---|---|---|
{slide2_rows}

</div>

<div class="rb-note mt-1">

{slide2_group_names}

</div>
{foot}{notes}
"""
        fname2 = "06-guidelines-2.md"
        (pages_dir / fname2).write_text(content_2, encoding="utf-8")
        filenames.append(fname2)

    return filenames


# ── Public entry point ──────────────────────────────────────────────────


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate architecture + guidelines slides for *phase*. Returns filenames."""
    written: list[str] = []
    arch_file = _render_architecture(project, phase, output_dir)
    if arch_file:
        written.append(arch_file)
    written.extend(_render_guidelines(project, phase, output_dir))
    return written
