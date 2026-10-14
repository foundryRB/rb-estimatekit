"""Slide renderer: phased delivery strategy."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

# CSS class per phase index — extends naturally for additional phases.
_CSS_CLASSES = [
    "cf-phase--demo",
    "cf-phase--p1",
    "cf-phase--p2",
    "cf-phase--p3",
]
_MAX_BULLETS = 6


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate the phased delivery strategy slide. Returns list of filenames."""
    if not project.phases:
        return []

    req_counts = project.count_requirements_per_phase()
    n_phases = len(project.phases)

    cols = ""
    for idx, phase in enumerate(project.phases):
        css_class = _CSS_CLASSES[idx] if idx < len(_CSS_CLASSES) else _CSS_CLASSES[-1]
        count = req_counts.get(phase.phase_id, 0)

        # Example bullets — split by comma, cap at _MAX_BULLETS
        examples = [e.strip() for e in phase.examples.split(",") if e.strip()]
        bullets = "\n".join(f"- {e}" for e in examples[:_MAX_BULLETS])

        desc_style = (
            'style="color:var(--cf-mid-grey);'
            'margin:0.15rem 0 0.4rem;"'
        )

        cols += f"""
<div class="cf-phase {css_class}">

### {phase.phase_name or phase.phase_id} \u2014 {phase.name}
**{count} reqs** \u00b7 _{phase.integration_type}_

<div class="text-xs" {desc_style}>{phase.description}</div>

{bullets}

</div>"""

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Phased Delivery Strategy

<div class="cf-divider"></div>

<div class="grid grid-cols-{n_phases} gap-3 mt-3 text-xs">
{cols}
</div>
{foot}{speaker_notes(phase, "delivery")}
"""

    filename = "05-phased-delivery.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return [filename]
