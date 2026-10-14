"""Use case: Delete a project file."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import FILE_DELETED, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class DeleteProjectFile:
    """Delete a data file from a project."""

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(self, project_path: Path, relative_path: str) -> None:
        """Remove the file at *relative_path*."""
        self._repository.delete_data_file(project_path, relative_path)
        logger.info("Deleted %s in %s", relative_path, project_path.name)
        state_fact(
            self._events,
            event_type=FILE_DELETED,
            subject=project_path.name,
            data={"project": project_path.name, "path": relative_path},
        )
