"""Mapper for scaffold-project responses."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.inbound.http.dtos.scaffold_response import ScaffoldProjectResponse


def map_scaffold_response(project_path: Path) -> ScaffoldProjectResponse:
    """Map the scaffolded project path to the response DTO."""
    return ScaffoldProjectResponse(slug=project_path.name, path=str(project_path))
