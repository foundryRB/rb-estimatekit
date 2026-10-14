"""File-system project repository — implements ProjectRepository.

Thin orchestrator that delegates to focused loader modules within
the persistence package.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from engine.adapters.outbound.persistence.config_loader import (
    load_config,
    save_config_data,
)
from engine.adapters.outbound.persistence.domain_loaders import (
    load_assumptions,
    load_guidelines,
)
from engine.adapters.outbound.persistence.phase_loaders import (
    load_build_activities,
    load_components,
    load_executive_summary,
    load_phase_config,
    load_phases,
    load_project_activities,
    load_resource_plan,
    load_resource_rows,
    load_slide_notes,
)
from engine.adapters.outbound.persistence.requirement_loaders import (
    load_brd_index,
    load_requirements,
)
from engine.domain.constants.files.inputs import (
    DATA_SUBDIRS,
    DIR_ACTIVITIES,
    DIR_ARCHITECTURE,
    DIR_ASSUMPTIONS,
    DIR_REQUIREMENTS,
    DIR_SLIDES,
)
from engine.domain.constants.files.markers import ARCHIVED_MARKER
from engine.domain.exceptions import (
    DataFileNotFoundError,
    InvalidPathError,
    OutputFileNotFoundError,
    ProjectAlreadyExistsError,
    ProjectLoadError,
    ProjectNotFoundError,
)
from engine.domain.model.aggregates.project import Project
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.data_file_export import DataFileExport
from engine.domain.model.value_objects.file_info import FileInfo
from engine.domain.model.value_objects.output_file_info import OutputFileInfo
from engine.logging import get_logger

logger = get_logger(__name__)


class FileProjectRepository:
    """Reads TSV/YAML files from disk → Project aggregate.

    Implements the ProjectRepository protocol.
    """

    def load(self, project_path: Path) -> Project:
        """Load all project data and construct the aggregate root."""
        if not (project_path / "project.yaml").exists():
            raise ProjectNotFoundError(project_path)
        try:
            return self._load_project(project_path)
        except ProjectNotFoundError:
            raise
        except Exception as exc:
            raise ProjectLoadError(project_path, str(exc)) from exc

    def _load_project(self, project_path: Path) -> Project:
        """Internal: load all project data without error wrapping."""
        data_dir = project_path / "data"
        req_dir = data_dir / DIR_REQUIREMENTS
        arch_dir = data_dir / DIR_ARCHITECTURE
        act_dir = data_dir / DIR_ACTIVITIES
        assume_dir = data_dir / DIR_ASSUMPTIONS
        slides_dir = data_dir / DIR_SLIDES

        config = load_config(project_path)
        phases = load_phases(req_dir)
        brd_order, req_to_cat = load_brd_index(req_dir)
        requirements = load_requirements(req_dir, phases)
        assumptions = load_assumptions(assume_dir)
        guidelines = load_guidelines(arch_dir)

        # Populate per-phase data, the pitch copy of the phase's deck included
        for phase in phases:
            phase.build_activities = load_build_activities(act_dir, phase.phase_id)
            phase.project_activities = load_project_activities(act_dir, phase.phase_id)
            phase.resource_plan = load_resource_plan(act_dir, phase.phase_id)
            phase.resource_rows = load_resource_rows(act_dir, phase.phase_id)
            phase.config = load_phase_config(act_dir, phase.phase_id)
            phase.components = load_components(arch_dir, phase.phase_id)
            phase.executive_summary = load_executive_summary(slides_dir, phase.phase_id)
            phase.slide_notes = load_slide_notes(slides_dir, phase.phase_id)
            # Inject BRD index for scheduling
            phase.brd_order = brd_order
            phase.req_to_category = req_to_cat

        return Project(
            config=config,
            phases=phases,
            requirements=requirements,
            assumptions=assumptions,
            guidelines=guidelines,
            source_path=project_path,
        )

    def exists(self, project_path: Path) -> bool:
        """Check whether a valid project exists at the given path."""
        return (project_path / "project.yaml").is_file()

    def delete(self, project_path: Path) -> None:
        """Delete a project directory and all its contents.

        Guarded by ``exists`` so only a real project directory (one holding
        a ``project.yaml``) is ever removed — never an arbitrary path.
        """
        if not self.exists(project_path):
            raise ProjectNotFoundError(project_path)
        shutil.rmtree(project_path)
        logger.info("Deleted project at %s", project_path)

    def rename(self, project_path: Path, new_project_path: Path) -> None:
        """Move a project directory to a new path in one atomic rename.

        Guarded by ``exists`` on the source (only a real project moves) and
        by an occupancy check on the target (an existing path is never
        overwritten). ``Path.rename`` is a single ``os.rename`` call, so the
        move is atomic within the projects root.
        """
        if not self.exists(project_path):
            raise ProjectNotFoundError(project_path)
        if new_project_path.exists():
            raise ProjectAlreadyExistsError(new_project_path)
        project_path.rename(new_project_path)
        logger.info("Renamed project directory %s to %s", project_path, new_project_path)

    def is_archived(self, project_path: Path) -> bool:
        """Check whether the project carries the archived marker file."""
        return (project_path / ARCHIVED_MARKER).is_file()

    def set_archived(self, project_path: Path, *, archived: bool) -> None:
        """Create or remove the archived marker file. Idempotent."""
        if not self.exists(project_path):
            raise ProjectNotFoundError(project_path)
        marker = project_path / ARCHIVED_MARKER
        if archived:
            marker.touch()
        else:
            marker.unlink(missing_ok=True)
        logger.info(
            "%s project at %s", "Archived" if archived else "Unarchived", project_path
        )

    def discover(self, projects_root: Path) -> list[Path]:
        """Find all project directories under a root path."""
        if not projects_root.is_dir():
            return []
        return sorted(
            p.parent for p in projects_root.rglob("project.yaml")
        )

    def save_config(self, project_path: Path, config: ProjectConfig) -> None:
        """Persist the project config to project.yaml."""
        save_config_data(project_path, config)

    def load_config(self, project_path: Path) -> ProjectConfig:
        """Load only the project config from project.yaml."""
        if not self.exists(project_path):
            raise ProjectNotFoundError(project_path)
        return load_config(project_path)

    _DATA_EXTENSIONS: set[str] = {".tsv", ".yaml", ".yml", ".puml", ".txt", ".md"}
    _KIND_MAP: dict[str, str] = {
        ".yaml": "yaml", ".yml": "yaml",
        ".tsv": "tsv",
        ".puml": "puml",
        ".txt": "text", ".md": "text",
    }

    def list_data_files(self, project_path: Path) -> list[FileInfo]:
        """List all editable data files in the project."""
        if not self.exists(project_path):
            raise ProjectNotFoundError(project_path)

        result: list[FileInfo] = []
        # Include project.yaml at the root
        root_yaml = project_path / "project.yaml"
        if root_yaml.is_file():
            result.append(FileInfo(
                path="project.yaml",
                name="project.yaml",
                kind="yaml",
                directory=".",
            ))

        # Scan data/ subdirectories (input) and output/roadmap/ (generated)
        data_root = project_path / "data"
        scan_dirs = [
            data_root / subdir for subdir in DATA_SUBDIRS
        ] + [
            project_path / "output" / "roadmap",
        ]

        for scan_dir in scan_dirs:
            if not scan_dir.is_dir():
                continue
            for file in sorted(scan_dir.rglob("*")):
                if file.is_file() and file.suffix.lower() in self._DATA_EXTENSIONS:
                    rel = file.relative_to(project_path)
                    result.append(FileInfo(
                        path=str(rel).replace("\\", "/"),
                        name=file.name,
                        kind=self._KIND_MAP.get(file.suffix.lower(), "text"),
                        directory=str(rel.parent).replace("\\", "/"),
                    ))
        return result

    def read_data_file(self, project_path: Path, relative_path: str) -> str:
        """Read the raw text content of a data file."""
        target = (project_path / relative_path).resolve()
        # Security: ensure target is within the project directory
        project_resolved = project_path.resolve()
        if not target.is_relative_to(project_resolved):
            raise InvalidPathError(relative_path)
        if not target.is_file():
            raise DataFileNotFoundError(Path(relative_path))
        return target.read_text(encoding="utf-8")

    def write_data_file(
        self, project_path: Path, relative_path: str, content: str,
    ) -> None:
        """Write raw text content to a data file."""
        target = (project_path / relative_path).resolve()
        project_resolved = project_path.resolve()
        if not target.is_relative_to(project_resolved):
            raise InvalidPathError(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def read_data_file_exact(self, project_path: Path, relative_path: str) -> str:
        """Read a data file's text with its line endings as stored."""
        target = (project_path / relative_path).resolve()
        if not target.is_relative_to(project_path.resolve()):
            raise InvalidPathError(relative_path)
        if not target.is_file():
            raise DataFileNotFoundError(Path(relative_path))
        return target.read_bytes().decode("utf-8")

    def write_data_file_exact(
        self, project_path: Path, relative_path: str, content: str,
    ) -> None:
        """Write text to a data file exactly as given, line endings untranslated."""
        target = (project_path / relative_path).resolve()
        if not target.is_relative_to(project_path.resolve()):
            raise InvalidPathError(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8"))

    def delete_data_file(self, project_path: Path, relative_path: str) -> None:
        """Delete a data file, with the same containment as read/write.

        Only recognised data files (the ``_DATA_EXTENSIONS`` allowlist) are
        removable; anything else, or a path with no file, is reported as a
        missing data file rather than silently ignored.
        """
        target = (project_path / relative_path).resolve()
        project_resolved = project_path.resolve()
        if not target.is_relative_to(project_resolved):
            raise InvalidPathError(relative_path)
        if target.suffix.lower() not in self._DATA_EXTENSIONS or not target.is_file():
            raise DataFileNotFoundError(Path(relative_path))
        target.unlink()

    def list_output_files(self, project_path: Path) -> list[OutputFileInfo]:
        """List all generated output files for the project."""
        if not self.exists(project_path):
            raise ProjectNotFoundError(project_path)

        output_dir = project_path / "output"
        if not output_dir.is_dir():
            return []

        pipeline_map = {"roadmap": "roadmap", "excel": "excel", "slides": "slides"}
        result: list[OutputFileInfo] = []
        for pipeline_dir_name, pipeline in pipeline_map.items():
            pipeline_dir = output_dir / pipeline_dir_name
            if not pipeline_dir.is_dir():
                continue
            for file in sorted(pipeline_dir.rglob("*")):
                if file.is_file():
                    rel = file.relative_to(project_path)
                    result.append(OutputFileInfo(
                        name=file.name,
                        pipeline=pipeline,
                        path=str(rel).replace("\\", "/"),
                        size=file.stat().st_size,
                    ))
        return result

    def resolve_output_file(self, project_path: Path, relative_path: str) -> Path:
        """Resolve and validate an output file path."""
        project_resolved = project_path.resolve()
        target = (project_resolved / "output" / relative_path).resolve()
        output_root = (project_resolved / "output").resolve()

        if not target.is_relative_to(output_root) or not target.is_file():
            raise OutputFileNotFoundError(Path(relative_path))

        return target

    def export_data_files(self, project_path: Path) -> list[DataFileExport]:
        """Read all data files and return their paths and raw content."""
        entries = self.list_data_files(project_path)
        result: list[DataFileExport] = []
        project_resolved = project_path.resolve()
        for fi in entries:
            abs_path = (project_path / fi.path).resolve()
            if abs_path.is_file() and abs_path.is_relative_to(project_resolved):
                result.append(DataFileExport(
                    path=fi.path,
                    content=abs_path.read_bytes(),
                ))
        return result

    def import_data_files(
        self, project_path: Path, files: dict[str, bytes],
    ) -> None:
        """Write data files with extension and path validation."""
        project_resolved = project_path.resolve()
        for relative_path, content in files.items():
            dest = (project_resolved / relative_path).resolve()
            # Security: skip paths that escape the project directory
            if not dest.is_relative_to(project_resolved):
                continue
            # Only write known data file extensions
            suffix = Path(relative_path).suffix.lower()
            if suffix not in self._DATA_EXTENSIONS:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
