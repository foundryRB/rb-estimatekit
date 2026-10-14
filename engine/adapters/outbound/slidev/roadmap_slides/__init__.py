"""Slide renderer: roadmap Gantt charts.

Generates the all-phases delivery roadmap slides and the sold phase's own
from domain model :class:`PhaseRoadmap` objects.

Slides produced (per entry in *roadmaps*):

  The sold phase (phase_id == the phase being sold):
    ``11-{idx}b-roadmap-{phase_id}.md``     — Activity Groups + Resource
    ``11-{idx}c-lifecycle-{phase_id}.md``   — Feature Lifecycle

  All-phases (phase_id == "All"), the context the sold phase sits in:
    ``10a-roadmap-all.md``                  — Activity Groups (compact)
    ``10b-lifecycle-all.md``                — Feature Lifecycle (compact)

  Other phases' roadmaps are context only and render no slide of their own.
"""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.adapters.outbound.slidev.roadmap_slides.slide_renderers import (
    render_activity_group_all_slide,
    render_activity_group_slide,
    render_lifecycle_all_slide,
    render_lifecycle_slide,
)
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

__all__ = ["render"]


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate roadmap Gantt chart slides for the deck selling *phase*. Returns filenames."""
    if not roadmaps:
        return []

    cfg = project.config
    primary = cfg.branding.primary_color
    foot = footer(cfg.name, cfg.branding.company)
    notes = speaker_notes(phase, "roadmap")
    n_phases = len(project.phases)

    # The project's actual phase-id set drives label parsing (never a fixed registry).
    phase_ids = [p.phase_id for p in project.phases]

    # Build phase-id → 1-based index map for filename ordering
    phase_index = {p.phase_id: i + 1 for i, p in enumerate(project.phases)}

    written: list[str] = []

    for roadmap in roadmaps:
        pid = roadmap.phase_id
        is_all = pid.lower() == "all"

        if is_all:
            # All-phases compact views (prefixed 10a/10b)
            fname = render_activity_group_all_slide(
                roadmap, n_phases, foot, output_dir,
                phase_ids=phase_ids, primary=primary, notes=notes,
            )
            if fname:
                written.append(fname)

            fname = render_lifecycle_all_slide(
                roadmap, n_phases, foot, output_dir,
                phase_ids=phase_ids, primary=primary, notes=notes,
            )
            if fname:
                written.append(fname)
        elif pid == phase.phase_id:
            # The sold phase's views (prefixed 11-{idx})
            idx = phase_index.get(pid, 0)
            fname = render_activity_group_slide(
                roadmap, foot, output_dir,
                phase_ids=phase_ids, primary=primary, phase_index=idx, notes=notes,
            )
            if fname:
                written.append(fname)

            fname = render_lifecycle_slide(
                roadmap, foot, output_dir,
                phase_ids=phase_ids, primary=primary, phase_index=idx, notes=notes,
            )
            if fname:
                written.append(fname)

    return written
