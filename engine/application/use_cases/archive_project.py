"""Use case: Archive a project, parking it out of the active listing."""

from __future__ import annotations

from pathlib import Path

from engine.application.events import PROJECT_ARCHIVED, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.logging import get_logger

logger = get_logger(__name__)


class ArchiveProject:
    """Archive a project: keep all data, drop it from the active listing."""

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(self, projects_root: Path, slug: str) -> Path:
        """Archive the project at *projects_root/slug*.

        Raises ProjectNotFoundError if the project does not exist.

        Returns the project's path.
        """
        target = projects_root / slug
        self._repository.set_archived(target, archived=True)
        logger.info("Archived project %s", slug)
        state_fact(self._events, event_type=PROJECT_ARCHIVED, subject=slug, data={"project": slug})
        return target
