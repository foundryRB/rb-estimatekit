"""Mapper for delete-project responses."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.inbound.http.dtos.delete_response import DeleteProjectResponse


def map_delete_response(project_path: Path) -> DeleteProjectResponse:
    """Map the deleted project path to the response DTO."""
    return DeleteProjectResponse(slug=project_path.name, deleted=True)
