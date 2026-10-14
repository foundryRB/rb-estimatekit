"""Slide renderer: executive summary."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.constants.files.inputs import SLIDES_EXECUTIVE_SUMMARY, slides_path
from engine.domain.exceptions import PhaseInputMissingError
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate the executive summary slide for *phase*. Returns list of filenames.

    The executive summary is the phase's pitch, so the phase being sold must
    carry one; a deck without it is refused.
    """
    es = phase.executive_summary
    if es is None or not phase.has_executive_summary:
        raise PhaseInputMissingError(
            phase.phase_id, slides_path(phase.phase_id, SLIDES_EXECUTIVE_SUMMARY),
        )

    # Context section
    context_bullets = "\n".join(f"- {b}" for b in es.context_bullets)
    context_block = f"""
<div class="text-sm" style="margin-bottom:0.8rem;">

{es.context_description}

{context_bullets}

</div>
"""

    td_key_style = (
        'style="font-weight:600;white-space:nowrap;'
        'vertical-align:top;padding-right:0.5rem;"'
    )

    # Rationale column
    rationale_rows = "\n".join(
        f'<tr><td {td_key_style}>{key}</td>'
        f'<td style="font-size:0.7rem;">{val}</td></tr>'
        for key, val in es.rationale
    )
    rationale_html = (
        '<div>\n'
        '<h4 style="margin:0 0 0.3rem;">Rationale</h4>\n'
        '<table style="width:100%;border-collapse:collapse;font-size:0.75rem;">\n'
        f'{rationale_rows}\n'
        '</table>\n'
        '</div>'
    )

    # Highlights column
    highlights_rows = "\n".join(
        f'<tr><td {td_key_style}>{key}</td>'
        f'<td style="font-size:0.7rem;">{val}</td></tr>'
        for key, val in es.highlights
    )
    highlights_html = (
        '<div>\n'
        '<h4 style="margin:0 0 0.3rem;">Highlights</h4>\n'
        '<table style="width:100%;border-collapse:collapse;font-size:0.75rem;">\n'
        f'{highlights_rows}\n'
        '</table>\n'
        '</div>'
    )

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Executive Summary <span class="text-sm text-gray-400">{phase.phase_id}</span>

<div class="rb-divider"></div>
{context_block}
<div class="grid grid-cols-2 gap-6">
{rationale_html}
{highlights_html}
</div>
{foot}{speaker_notes(phase, "executive-summary")}
"""

    filename = "02-executive-summary.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return [filename]
