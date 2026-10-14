"""Use case: Write content to a project file."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import FILE_WRITTEN, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class WriteProjectFile:
    """Write (create or overwrite) a data file in a project."""

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(self, project_path: Path, relative_path: str, content: str) -> None:
        """Write *content* to the file at *relative_path*."""
        self._repository.write_data_file(project_path, relative_path, content)
        logger.info("Wrote %s in %s", relative_path, project_path.name)
        state_fact(
            self._events,
            event_type=FILE_WRITTEN,
            subject=project_path.name,
            data={"project": project_path.name, "path": relative_path},
        )
