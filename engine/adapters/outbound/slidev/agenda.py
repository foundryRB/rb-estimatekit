"""Slide renderer: agenda."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.man_days import format_md
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate the agenda slide. Returns list of page filenames written."""
    n_reqs = len(project.requirements)
    n_assumptions = len(project.assumptions)
    n_guidelines = len(project.guidelines_for(phase.phase_id))
    n_phases = len(project.phases)

    # Compute total and per-phase effort strings
    total_md = sum(e.authored_total for e in efforts.values())
    phase_parts = " · ".join(
        f"{pid}: {format_md(eff.authored_total)}"
        for pid, eff in efforts.items()
    )
    total_str = format_md(total_md)

    # Build numbered agenda items dynamically
    items: list[str] = []
    items.append(
        "**Executive Summary** — Project scope & strategic context"
    )
    items.append(
        f"**Requirements Overview** — {n_reqs} requirements by category"
    )
    items.append(
        f"**Requirements × Phase Matrix** — Distribution across {n_phases} phases"
    )
    items.append(
        f"**Phased Delivery Strategy** — {n_phases}-phase approach"
    )
    items.append(
        "**Architecture & Infrastructure** — System design & platform overview"
    )
    if n_guidelines:
        items.append(
            f"**Architecture Guidelines** — {n_guidelines} governing decisions"
        )
    items.append(
        f"**Assumptions** — {n_assumptions} assumptions with confidence ratings"
    )
    items.append(
        "**Assumption Risk Map** — Every assumption by confidence and impact"
    )
    items.append(
        f"**Effort Estimate** — {total_str} MD ({phase_parts})"
    )
    items.append(
        "**Effort Breakdown** — Per-phase build + overhead analysis"
    )
    items.append(
        "**Delivery Roadmap** — Gantt timeline with milestones across all phases"
    )
    items.append(
        "**Cost Summary** — Very Rough Order of Magnitude by phase"
    )

    numbered = "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Agenda

<div class="cf-divider"></div>

{numbered}
{foot}{speaker_notes(phase, "agenda")}
"""

    filename = "01-agenda.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return [filename]
