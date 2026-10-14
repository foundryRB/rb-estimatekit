"""Response DTO for listing project data files."""

from __future__ import annotations

from pydantic import BaseModel


class FileInfoItem(BaseModel):
    """Single data file entry."""

    path: str
    name: str
    kind: str
    directory: str


class ListFilesResponse(BaseModel):
    """Response for ``GET /api/projects/{slug}/files``."""

    files: list[FileInfoItem]
