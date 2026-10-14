"""Use case: Discover available projects."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.model.value_objects.discovered_project import DiscoveredProject
from engine.logging import get_logger

logger = get_logger(__name__)


class DiscoverProjects:
    """Find all valid projects under a root directory."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, projects_root: Path) -> list[DiscoveredProject]:
        """Return every discovered project with its archived state."""
        found = self._repository.discover(projects_root)
        entries = [
            DiscoveredProject(path=path, archived=self._repository.is_archived(path))
            for path in found
        ]
        logger.debug("Discovered %d project(s) under %s", len(entries), projects_root)
        return entries
