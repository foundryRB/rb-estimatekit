"""Mapper for archive- and unarchive-project responses."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.inbound.http.dtos.archive_response import ArchiveProjectResponse


def map_archive_response(project_path: Path, *, archived: bool) -> ArchiveProjectResponse:
    """Map the project path and its new archived state to the response DTO."""
    return ArchiveProjectResponse(slug=project_path.name, archived=archived)
