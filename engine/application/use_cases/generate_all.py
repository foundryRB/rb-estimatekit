"""Use case: Generate all outputs for a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import ARTIFACT_GENERATED, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.excel_writer import ExcelWriter
from engine.application.ports.outbound.presentation_writer import PresentationWriter
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.application.ports.outbound.roadmap_writer import RoadmapWriter
from engine.application.ports.outbound.slides_builder import SlidesBuilder
from engine.domain.model.value_objects.generation_result import GenerationResult
from engine.domain.model.value_objects.pipeline import Pipeline
from engine.domain.services.phase_selection import select_phase_with_pitch
from engine.domain.services.roadmap_merger import merge_roadmaps
from engine.logging import get_logger

logger = get_logger(__name__)


class GenerateAll:
    """Orchestrate full generation pipeline — roadmap, excels, slides."""

    def __init__(
        self,
        repository: ProjectRepository,
        roadmap_writer: RoadmapWriter,
        excel_writer: ExcelWriter,
        presentation_writer: PresentationWriter,
        slides_builder: SlidesBuilder | None = None,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._roadmap_writer = roadmap_writer
        self._excel_writer = excel_writer
        self._presentation_writer = presentation_writer
        self._slides_builder = slides_builder
        self._events = events

    def execute(
        self,
        project_path: Path,
        *,
        pipelines: list[Pipeline] | None = None,
        phase: str | None = None,
        slides_base_path: str = "/",
    ) -> GenerationResult:
        """Run selected generation pipelines.

        The slide deck sells one phase, *phase*. It is resolved, and its pitch
        checked, before any pipeline writes, so a request the project cannot
        answer (several phases and none named, an unknown one, or a phase
        without its executive summary) leaves every output as it was.
        """
        targets = pipelines or list(Pipeline)
        project = self._repository.load(project_path)
        sold = select_phase_with_pitch(project, phase) if Pipeline.SLIDES in targets else None
        output_dir = project_path / "output"
        outcomes: dict[Pipeline, bool] = {}

        # Schedule per-phase roadmaps — used by roadmap and slides pipelines
        roadmaps = project.schedule_all_roadmaps()

        if Pipeline.ROADMAP in targets:
            roadmap_dir = output_dir / "roadmap"
            for rm in roadmaps:
                self._roadmap_writer.write_phase(roadmap_dir, rm)
            if roadmaps:
                self._roadmap_writer.write_merged(roadmap_dir, roadmaps)
            outcomes[Pipeline.ROADMAP] = True

        if Pipeline.EXCEL in targets:
            self._excel_writer.write_all(project, output_dir / "excel")
            outcomes[Pipeline.EXCEL] = True

        if sold is not None:
            efforts = project.compute_all_efforts()
            slides_dir = output_dir / "slides"
            # Slides need a merged "All" PhaseRoadmap for overall Gantt charts
            slide_roadmaps = (
                roadmaps + [merge_roadmaps(roadmaps)]
                if len(roadmaps) >= 2
                else list(roadmaps)
            )
            self._presentation_writer.write_deck(
                project, sold, efforts, slide_roadmaps, slides_dir,
            )
            # Build static HTML from the generated Slidev markdown. A wired
            # builder that fails must fail the pipeline; no builder at all is
            # markdown-only mode and still counts as success.
            built = True
            if self._slides_builder:
                built = self._slides_builder.build(slides_dir, base_path=slides_base_path)
            outcomes[Pipeline.SLIDES] = built

        result = GenerationResult(
            outcomes=outcomes, phase=sold.phase_id if sold is not None else None,
        )
        logger.info(
            "Generation for %s: %s",
            project_path.name,
            ", ".join(f"{p.value}={'ok' if ok else 'FAILED'}" for p, ok in outcomes.items()),
        )
        # One fact per artifact that exists: a pipeline that failed produced
        # nothing to state. The artifact is named by kind; its bytes are fetched
        # from the engine's output listing (REF-Events section 5).
        for pipeline, ok in outcomes.items():
            if ok:
                state_fact(
                    self._events,
                    event_type=ARTIFACT_GENERATED,
                    subject=project_path.name,
                    data={"project": project_path.name, "artifact": pipeline.value},
                )
        return result
