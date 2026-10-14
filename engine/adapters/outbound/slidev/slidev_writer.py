"""Slidev writer — implements PresentationWriter port.

Orchestrates all individual slide renderers and the scaffold generator
to produce the complete Slidev presentation deck.
"""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.slidev import (
    agenda,
    architecture,
    assumptions,
    delivery,
    effort,
    executive_summary,
    requirements,
    roadmap_slides,
    vrom,
)
from engine.adapters.outbound.slidev.scaffold import (
    write_slides_md,
    write_style_css,
)
from engine.domain.exceptions import AppError, GenerationError
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_id import PhaseId
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap
from engine.logging import get_logger

logger = get_logger(__name__)

# Renderers are called in slide-deck order.
_RENDERERS = [
    executive_summary,
    agenda,
    requirements,
    delivery,
    architecture,
    assumptions,
    effort,
    roadmap_slides,
    vrom,
]


class SlidevWriter:
    """Generate a Slidev presentation deck from domain objects.

    Implements the PresentationWriter port. The deck sells one phase: its
    pitch, architecture and per-phase sections are that phase's, and the
    cross-phase slides (requirements, phased delivery, effort summary, the
    all-phases roadmap, cost) give the context it sits in.
    """

    def write_deck(
        self,
        project: Project,
        phase: Phase,
        efforts: dict[PhaseId, PhaseEffort],
        roadmaps: list[PhaseRoadmap],
        output_dir: Path,
    ) -> int:
        """Write the slide deck that sells *phase* to the output directory.

        1. Empty pages/ of its *.md pages, so it holds exactly this deck's pages
        2. Generate each slide page to pages/*.md
        3. Generate scaffold (slides.md, style.css)
        4. Return the number of pages written.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        pages_dir = output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        for page in pages_dir.glob("*.md"):
            page.unlink()

        page_files: list[str] = []

        for renderer in _RENDERERS:
            try:
                files = renderer.render(project, phase, efforts, roadmaps, output_dir)
                page_files.extend(files)
            except AppError:
                raise
            except Exception as exc:
                raise GenerationError(renderer.__name__, str(exc)) from exc

        # Sort page files by filename to ensure correct deck ordering
        page_files.sort()

        # Generate scaffold files
        write_slides_md(output_dir, project.config, phase, page_files)
        write_style_css(output_dir, project.config.branding)

        logger.info("✓ %d slide pages generated for %s", len(page_files), phase.phase_id)
        return len(page_files)
