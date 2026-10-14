"""Composition root — the single place where all layers are wired together.

Both inbound adapters (CLI and HTTP) use this container to get fully
configured use cases through inbound port interfaces.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TypeVar

from engine.adapters.outbound.auditor.pytest_auditor_runner import PytestAuditorRunner
from engine.adapters.outbound.auditor.tsv_suggestion_analyzer import TsvSuggestionAnalyzer
from engine.adapters.outbound.events import resolve_event_publisher
from engine.adapters.outbound.excel.excel_writer import OpenpyxlExcelWriter
from engine.adapters.outbound.persistence.file_project_repository import FileProjectRepository
from engine.adapters.outbound.persistence.file_template_repository import FileTemplateRepository
from engine.adapters.outbound.plantuml.plantuml_renderer import PlantUmlRenderer
from engine.adapters.outbound.roadmap.tsv_roadmap_writer import TsvRoadmapWriter
from engine.adapters.outbound.slidev.slidev_builder import SlidevBuilder
from engine.adapters.outbound.slidev.slidev_writer import SlidevWriter
from engine.application.ports.inbound.append_project_rows import AppendProjectRowsPort
from engine.application.ports.inbound.archive_project import ArchiveProjectPort
from engine.application.ports.inbound.delete_project import DeleteProjectPort
from engine.application.ports.inbound.delete_project_file import DeleteProjectFilePort
from engine.application.ports.inbound.discover_projects import DiscoverProjectsPort
from engine.application.ports.inbound.download_output_file import DownloadOutputFilePort
from engine.application.ports.inbound.export_project import ExportProjectPort
from engine.application.ports.inbound.generate_all import GenerateAllPort
from engine.application.ports.inbound.generate_excels import GenerateExcelsPort
from engine.application.ports.inbound.generate_roadmap import GenerateRoadmapPort
from engine.application.ports.inbound.generate_slides import GenerateSlidesPort
from engine.application.ports.inbound.get_project_summary import GetProjectSummaryPort
from engine.application.ports.inbound.import_project import ImportProjectPort
from engine.application.ports.inbound.list_architecture_diagrams import (
    ListArchitectureDiagramsPort,
)
from engine.application.ports.inbound.list_output_files import ListOutputFilesPort
from engine.application.ports.inbound.list_project_files import ListProjectFilesPort
from engine.application.ports.inbound.read_project_file import ReadProjectFilePort
from engine.application.ports.inbound.rename_project import RenameProjectPort
from engine.application.ports.inbound.render_architecture_diagram import (
    RenderArchitectureDiagramPort,
)
from engine.application.ports.inbound.replace_project_row import ReplaceProjectRowPort
from engine.application.ports.inbound.run_audit import RunAuditPort
from engine.application.ports.inbound.scaffold_phase import ScaffoldPhasePort
from engine.application.ports.inbound.scaffold_project import ScaffoldProjectPort
from engine.application.ports.inbound.unarchive_project import UnarchiveProjectPort
from engine.application.ports.inbound.write_project_file import WriteProjectFilePort
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.use_cases.append_project_rows import AppendProjectRows
from engine.application.use_cases.archive_project import ArchiveProject
from engine.application.use_cases.delete_project import DeleteProject
from engine.application.use_cases.delete_project_file import DeleteProjectFile
from engine.application.use_cases.discover_projects import DiscoverProjects
from engine.application.use_cases.download_output_file import DownloadOutputFile
from engine.application.use_cases.export_project import ExportProject
from engine.application.use_cases.generate_all import GenerateAll
from engine.application.use_cases.generate_excels import GenerateExcels
from engine.application.use_cases.generate_roadmap import GenerateRoadmap
from engine.application.use_cases.generate_slides import GenerateSlides
from engine.application.use_cases.get_project_summary import GetProjectSummary
from engine.application.use_cases.import_project import ImportProject
from engine.application.use_cases.list_architecture_diagrams import ListArchitectureDiagrams
from engine.application.use_cases.list_output_files import ListOutputFiles
from engine.application.use_cases.list_project_files import ListProjectFiles
from engine.application.use_cases.read_project_file import ReadProjectFile
from engine.application.use_cases.rename_project import RenameProject
from engine.application.use_cases.render_architecture_diagram import RenderArchitectureDiagram
from engine.application.use_cases.replace_project_row import ReplaceProjectRow
from engine.application.use_cases.run_audit import RunAudit
from engine.application.use_cases.scaffold_phase import ScaffoldPhase
from engine.application.use_cases.scaffold_project import ScaffoldProject
from engine.application.use_cases.unarchive_project import UnarchiveProject
from engine.application.use_cases.write_project_file import WriteProjectFile


class Container:
    """Dependency injection container — wires outbound adapters to use cases.

    Factory methods return **inbound port** types, hiding the concrete
    use case implementations from callers.

    Usage::

        container = Container()
        result = container.generate_all().execute(project_path)
    """

    def __init__(
        self,
        templates_dir: Path | None = None,
        projects_root: Path | None = None,
        events: EventPublisher | None = None,
    ) -> None:
        # Resolve default templates directory relative to workspace
        self._templates_dir = templates_dir or Path(__file__).parent.parent / "templates"

        # Resolve projects root from explicit arg, env var, or conventional default
        self._projects_root = (projects_root or self._default_projects_root()).resolve()

        # Instantiate outbound adapters (shared across use cases)
        self._project_repo = FileProjectRepository()
        self._template_repo = FileTemplateRepository(self._templates_dir)
        self._roadmap_writer = TsvRoadmapWriter()
        self._excel_writer = OpenpyxlExcelWriter()
        self._presentation_writer = SlidevWriter()
        self._slides_builder = SlidevBuilder()
        self._auditor_runner = PytestAuditorRunner()
        self._suggestion_analyzer = TsvSuggestionAnalyzer()
        self._diagram_renderer = PlantUmlRenderer()
        # The event bus this engine's grant reached, or the logging publisher when
        # there is none; either way every act completes unchanged (REF-Events).
        self._events: EventPublisher = events or resolve_event_publisher()

    @staticmethod
    def _default_projects_root() -> Path:
        """Determine the projects root from env var or conventional default."""
        env = os.environ.get("ESTIMATEKIT_PROJECTS_ROOT")
        if env:
            return Path(env).resolve()
        # Default: <workspace>/projects  (workspace = modern/)
        return (Path(__file__).resolve().parents[1] / "projects").resolve()

    @property
    def projects_root(self) -> Path:
        """Return the resolved, server-side projects root directory."""
        return self._projects_root

    def project_path(self, slug: str) -> Path:
        """Validate *slug* as a :class:`ProjectSlug` and return its full path."""
        from engine.domain.model.value_objects.project_slug import ProjectSlug

        return self._projects_root / str(ProjectSlug(slug))

    def scaffold_project(self) -> ScaffoldProjectPort:
        return _check(
            ScaffoldProject(templates=self._template_repo, events=self._events),
            ScaffoldProjectPort,
        )

    def scaffold_phase(self) -> ScaffoldPhasePort:
        return _check(
            ScaffoldPhase(
                repository=self._project_repo,
                templates=self._template_repo,
                events=self._events,
            ),
            ScaffoldPhasePort,
        )

    def generate_roadmap(self) -> GenerateRoadmapPort:
        return _check(
            GenerateRoadmap(repository=self._project_repo, writer=self._roadmap_writer),
            GenerateRoadmapPort,
        )

    def generate_excels(self) -> GenerateExcelsPort:
        return _check(
            GenerateExcels(repository=self._project_repo, writer=self._excel_writer),
            GenerateExcelsPort,
        )

    def generate_slides(self) -> GenerateSlidesPort:
        return _check(
            GenerateSlides(
                repository=self._project_repo,
                roadmap_writer=self._roadmap_writer,
                presentation_writer=self._presentation_writer,
            ),
            GenerateSlidesPort,
        )

    def generate_all(self) -> GenerateAllPort:
        return _check(
            GenerateAll(
                repository=self._project_repo,
                roadmap_writer=self._roadmap_writer,
                excel_writer=self._excel_writer,
                presentation_writer=self._presentation_writer,
                slides_builder=self._slides_builder,
                events=self._events,
            ),
            GenerateAllPort,
        )

    def discover_projects(self) -> DiscoverProjectsPort:
        return _check(DiscoverProjects(repository=self._project_repo), DiscoverProjectsPort)

    def delete_project(self) -> DeleteProjectPort:
        return _check(
            DeleteProject(repository=self._project_repo, events=self._events), DeleteProjectPort
        )

    def rename_project(self) -> RenameProjectPort:
        return _check(
            RenameProject(repository=self._project_repo, events=self._events), RenameProjectPort
        )

    def archive_project(self) -> ArchiveProjectPort:
        return _check(
            ArchiveProject(repository=self._project_repo, events=self._events), ArchiveProjectPort
        )

    def unarchive_project(self) -> UnarchiveProjectPort:
        return _check(
            UnarchiveProject(repository=self._project_repo, events=self._events),
            UnarchiveProjectPort,
        )

    def get_project_summary(self) -> GetProjectSummaryPort:
        return _check(GetProjectSummary(repository=self._project_repo), GetProjectSummaryPort)

    def list_project_files(self) -> ListProjectFilesPort:
        return _check(ListProjectFiles(repository=self._project_repo), ListProjectFilesPort)

    def read_project_file(self) -> ReadProjectFilePort:
        return _check(ReadProjectFile(repository=self._project_repo), ReadProjectFilePort)

    def write_project_file(self) -> WriteProjectFilePort:
        return _check(
            WriteProjectFile(repository=self._project_repo, events=self._events),
            WriteProjectFilePort,
        )

    def append_project_rows(self) -> AppendProjectRowsPort:
        return _check(
            AppendProjectRows(repository=self._project_repo, events=self._events),
            AppendProjectRowsPort,
        )

    def replace_project_row(self) -> ReplaceProjectRowPort:
        return _check(
            ReplaceProjectRow(repository=self._project_repo, events=self._events),
            ReplaceProjectRowPort,
        )

    def delete_project_file(self) -> DeleteProjectFilePort:
        return _check(
            DeleteProjectFile(repository=self._project_repo, events=self._events),
            DeleteProjectFilePort,
        )

    def list_architecture_diagrams(self) -> ListArchitectureDiagramsPort:
        return _check(
            ListArchitectureDiagrams(repository=self._project_repo),
            ListArchitectureDiagramsPort,
        )

    def render_architecture_diagram(self) -> RenderArchitectureDiagramPort:
        return _check(
            RenderArchitectureDiagram(
                repository=self._project_repo,
                renderer=self._diagram_renderer,
            ),
            RenderArchitectureDiagramPort,
        )

    def list_output_files(self) -> ListOutputFilesPort:
        return _check(ListOutputFiles(repository=self._project_repo), ListOutputFilesPort)

    def download_output_file(self) -> DownloadOutputFilePort:
        return _check(DownloadOutputFile(repository=self._project_repo), DownloadOutputFilePort)

    def export_project(self) -> ExportProjectPort:
        return _check(ExportProject(repository=self._project_repo), ExportProjectPort)

    def import_project(self) -> ImportProjectPort:
        return _check(ImportProject(repository=self._project_repo), ImportProjectPort)

    def run_audit(self) -> RunAuditPort:
        return _check(
            RunAudit(
                runner=self._auditor_runner,
                suggestions=self._suggestion_analyzer,
                events=self._events,
            ),
            RunAuditPort,
        )

    def read_guide(self) -> dict[str, Any]:
        """Return parsed guide content from templates."""
        return self._template_repo.read_guide()


_T = TypeVar("_T")


def _check(instance: object, port: type[_T]) -> _T:
    """Assert that *instance* satisfies *port* at runtime.

    Raises :class:`TypeError` immediately if the use case does not
    implement the inbound port protocol — catching signature drift
    before any caller invokes ``execute()``.
    """
    if not isinstance(instance, port):
        msg = f"{type(instance).__name__} does not satisfy {port.__name__}"
        raise TypeError(msg)
    return instance  # type: ignore[return-value]
