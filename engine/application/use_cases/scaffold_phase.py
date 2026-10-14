"""Use case: Mint a new phase in an existing project from the templates."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import FILE_WRITTEN, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.application.ports.outbound.template_repository import TemplateRepository
from engine.domain.constants.columns import COL_NOTES, COL_PHASE_ID
from engine.domain.constants.files.inputs import (
    DIR_DATA,
    DIR_REQUIREMENTS,
    FILE_MATRIX,
    FILE_PHASES,
)
from engine.domain.exceptions import (
    InvalidPhaseIdError,
    PhaseAlreadyExistsError,
    ProjectNotFoundError,
)
from engine.domain.services.phase_files import (
    PHASE_ID_PATTERN,
    phase_display_name,
    phase_table_row,
)
from engine.domain.services.tsv_text import (
    append_row,
    column_values,
    has_column,
    header_of,
    insert_column,
)
from engine.logging import get_logger

logger = get_logger(__name__)


class ScaffoldPhase:
    """Add a phase to a project the way the scaffold adds a project.

    The phase's row lands in the phase table and its column in the matrix,
    and its whole file set (activities, architecture, pitch copy) is copied
    from the templates, every example value sentinel-marked. The audit then
    refuses the phase until each file is authored or deleted.
    """

    def __init__(
        self,
        repository: ProjectRepository,
        templates: TemplateRepository,
        events: EventPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._templates = templates
        self._events = events

    def execute(self, project_path: Path, phase_id: str, *, force: bool = False) -> list[str]:
        """Mint *phase_id*. Returns the project-relative paths written."""
        if not PHASE_ID_PATTERN.match(phase_id):
            raise InvalidPhaseIdError(phase_id)
        if not self._repository.exists(project_path):
            raise ProjectNotFoundError(project_path)

        existing = [
            info.path
            for info in self._repository.list_data_files(project_path)
            if Path(info.path).name.startswith(f"{phase_id}-")
        ]
        if existing and not force:
            raise PhaseAlreadyExistsError(phase_id, existing)

        written: list[str] = []
        written.extend(self._define_phase(project_path, phase_id))
        data_dir = project_path / DIR_DATA
        written.extend(
            f"{DIR_DATA}/{rel}"
            for rel in self._templates.scaffold_phase_to(data_dir, phase_id, force=force)
        )

        logger.info("Minted phase %s in %s: %d file(s)", phase_id, project_path.name, len(written))
        for path in written:
            state_fact(
                self._events,
                event_type=FILE_WRITTEN,
                subject=project_path.name,
                data={"project": project_path.name, "path": path},
            )
        return written

    def _define_phase(self, project_path: Path, phase_id: str) -> list[str]:
        """Give the phase its row in the phase table and its column in the matrix."""
        written: list[str] = []

        phases_rel = f"{DIR_DATA}/{DIR_REQUIREMENTS}/{FILE_PHASES}"
        phases_text = self._repository.read_data_file(project_path, phases_rel)
        if phase_id not in column_values(phases_text, COL_PHASE_ID):
            row = phase_table_row(header_of(phases_text), phase_id)
            self._repository.write_data_file(project_path, phases_rel, append_row(phases_text, row))
            written.append(phases_rel)

        matrix_rel = f"{DIR_DATA}/{DIR_REQUIREMENTS}/{FILE_MATRIX}"
        matrix_text = self._repository.read_data_file(project_path, matrix_rel)
        display_name = phase_display_name(phase_id)
        if not has_column(matrix_text, display_name):
            widened = insert_column(matrix_text, display_name, before=COL_NOTES)
            self._repository.write_data_file(project_path, matrix_rel, widened)
            written.append(matrix_rel)

        return written
