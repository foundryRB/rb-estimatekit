"""Mapper for architecture diagram responses."""

from __future__ import annotations

from engine.adapters.inbound.http.dtos.diagram_svg_response import DiagramSvgResponse
from engine.adapters.inbound.http.dtos.list_diagrams_response import (
    DiagramInfoItem,
    ListDiagramsResponse,
)
from engine.domain.model.value_objects.file_info import FileInfo


def map_list_diagrams_response(diagrams: list[FileInfo]) -> ListDiagramsResponse:
    """Map domain FileInfo list to HTTP response DTO."""
    return ListDiagramsResponse(
        diagrams=[DiagramInfoItem(name=d.name, path=d.path) for d in diagrams]
    )


def map_diagram_svg_response(name: str, svg: str) -> DiagramSvgResponse:
    """Map a rendered diagram to HTTP response DTO."""
    return DiagramSvgResponse(name=name, svg=svg)
