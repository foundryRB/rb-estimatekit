"""Use case: Render one architecture diagram to SVG, on demand."""

from __future__ import annotations

from pathlib import Path

from engine.application.ports.outbound.diagram_renderer import DiagramRenderer
from engine.application.ports.outbound.project_repository import ProjectRepository
from engine.domain.constants.files.inputs import ARCHITECTURE_DATA_DIR, SUFFIX_DIAGRAM
from engine.domain.exceptions import DataFileNotFoundError
from engine.logging import get_logger

logger = get_logger(__name__)


class RenderArchitectureDiagram:
    """Read one PlantUML source from the project and render it to SVG."""

    def __init__(self, repository: ProjectRepository, renderer: DiagramRenderer) -> None:
        self._repository = repository
        self._renderer = renderer

    def execute(self, project_path: Path, name: str) -> str:
        """Return the SVG document for the named diagram.

        ``name`` is a bare diagram filename (the ``.puml`` suffix is
        optional), resolved inside the project's architecture folder only.
        """
        filename = name if name.endswith(SUFFIX_DIAGRAM) else f"{name}{SUFFIX_DIAGRAM}"
        if Path(filename).name != filename:
            raise DataFileNotFoundError(
                Path(filename), hint="a diagram name is a bare filename"
            )
        source = self._repository.read_data_file(
            project_path, f"{ARCHITECTURE_DATA_DIR}/{filename}"
        )
        svg = self._renderer.render_svg(source)
        logger.info("Rendered architecture diagram %s in %s", filename, project_path.name)
        return svg
