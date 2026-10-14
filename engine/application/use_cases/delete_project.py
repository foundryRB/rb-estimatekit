"""Use case: Delete a project and all its data."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import PROJECT_DELETED, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class DeleteProject:
    """Permanently remove a project directory and all its contents."""

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(self, projects_root: Path, slug: str) -> Path:
        """Delete the project at *projects_root/slug*.

        Raises ProjectNotFoundError if the project does not exist.

        Returns the path that was removed.
        """
        target = projects_root / slug
        self._repository.delete(target)
        logger.info("Deleted project %s", slug)
        state_fact(self._events, event_type=PROJECT_DELETED, subject=slug, data={"project": slug})
        return target
