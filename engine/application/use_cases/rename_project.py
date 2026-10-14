"""Use case: Rename a project's display name and/or slug."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from engine.application.events import PROJECT_RENAMED, state_fact
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.exceptions import InvalidRenameError
from engine.domain.model.value_objects.project_slug import ProjectSlug
from engine.logging import get_logger

logger = get_logger(__name__)


class RenameProject:
    """Rename a project: its display name, its slug, or both.

    A slug rename moves the project directory in one atomic filesystem
    rename, so the project stops answering under the old slug the moment
    it answers under the new one.
    """

    def __init__(
        self, repository: ProjectRepository, events: EventPublisher | None = None
    ) -> None:
        self._repository = repository
        self._events = events

    def execute(
        self,
        projects_root: Path,
        slug: str,
        *,
        new_slug: str | None = None,
        new_name: str | None = None,
    ) -> Path:
        """Rename the project at *projects_root/slug*.

        Raises InvalidRenameError when neither new_slug nor new_name is
        given, InvalidSlugError for a malformed target slug,
        ProjectNotFoundError if the project does not exist, and
        ProjectAlreadyExistsError if the target slug is occupied.

        Returns the project's path after the rename.
        """
        if new_slug is None and new_name is None:
            raise InvalidRenameError(slug)

        target = projects_root / slug
        if new_slug is not None and new_slug != slug:
            new_target = projects_root / str(ProjectSlug(new_slug))
            self._repository.rename(target, new_target)
            logger.info("Renamed project slug %s to %s", slug, new_target.name)
            target = new_target

        if new_name is not None:
            config = self._repository.load_config(target)
            self._repository.save_config(target, replace(config, name=new_name))
            logger.info("Renamed project %s display name to %s", target.name, new_name)

        state_fact(
            self._events,
            event_type=PROJECT_RENAMED,
            subject=target.name,
            data={"project": target.name, "previous": slug, "name_changed": new_name is not None},
        )
        return target
