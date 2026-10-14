"""Routes: architecture diagram listing and on-demand, in-process SVG rendering."""

from __future__ import annotations

import asyncio
from functools import partial

from fastapi import APIRouter, Depends

from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.dtos.diagram_svg_response import DiagramSvgResponse
from engine.adapters.inbound.http.dtos.list_diagrams_response import ListDiagramsResponse
from engine.adapters.inbound.http.mappers.diagrams_mapper import (
    map_diagram_svg_response,
    map_list_diagrams_response,
)
from engine.container import Container

router = APIRouter()


@router.get("/{slug}/architecture/diagrams", response_model=ListDiagramsResponse)
async def list_diagrams(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> ListDiagramsResponse:
    """List the project's architecture diagram sources (.puml files)."""
    project_path = container.project_path(slug)
    diagrams = container.list_architecture_diagrams().execute(project_path)
    return map_list_diagrams_response(diagrams)


@router.get("/{slug}/architecture/diagrams/{name}", response_model=DiagramSvgResponse)
async def render_diagram(
    slug: str,
    name: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> DiagramSvgResponse:
    """Render one architecture diagram to SVG inside this process."""
    project_path = container.project_path(slug)

    # The render shells a local PlantUML process; run it in a thread so the
    # event loop stays free (same pattern as the generation pipelines).
    loop = asyncio.get_running_loop()
    svg = await loop.run_in_executor(
        None,
        partial(container.render_architecture_diagram().execute, project_path, name),
    )

    return map_diagram_svg_response(name, svg)
