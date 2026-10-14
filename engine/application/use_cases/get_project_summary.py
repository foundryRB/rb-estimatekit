"""Use case: Get a lightweight summary of a project."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.model.value_objects.project_summary import ProjectSummary
from engine.logging import get_logger

logger = get_logger(__name__)


class GetProjectSummary:
    """Load a project and return a lightweight summary."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_path: Path) -> ProjectSummary:
        """Load the project and extract summary information."""
        project = self._repository.load(project_path)
        logger.debug("Summarised project %s", project_path.name)
        return ProjectSummary(
            name=project.config.name,
            client=project.config.client,
            description=project.config.description,
            phase_count=len(project.phases),
            requirement_count=len(project.requirements),
            assumption_count=len(project.assumptions),
            archived=self._repository.is_archived(project_path),
            phases=[phase.phase_id for phase in project.phases],
        )
