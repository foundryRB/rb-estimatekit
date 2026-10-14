"""Mapper for rename-project responses."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.inbound.http.dtos.rename_response import RenameProjectResponse


def map_rename_response(slug: str, new_path: Path) -> RenameProjectResponse:
    """Map the original slug and the renamed project path to the response DTO."""
    return RenameProjectResponse(slug=slug, new_slug=new_path.name, renamed=True)
