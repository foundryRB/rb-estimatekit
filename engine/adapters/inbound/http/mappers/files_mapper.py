"""Mapper for file-related responses."""

from __future__ import annotations

from engine.adapters.inbound.http.dtos.file_content_response import FileContentResponse
from engine.adapters.inbound.http.dtos.list_files_response import FileInfoItem, ListFilesResponse
from engine.adapters.inbound.http.dtos.list_outputs_response import (
    ListOutputsResponse,
    OutputFileItem,
)
from engine.domain.model.value_objects.file_info import FileInfo
from engine.domain.model.value_objects.output_file_info import OutputFileInfo


def map_list_files_response(files: list[FileInfo]) -> ListFilesResponse:
    """Map domain FileInfo list to HTTP response DTO."""
    return ListFilesResponse(
        files=[
            FileInfoItem(
                path=f.path,
                name=f.name,
                kind=f.kind,
                directory=f.directory,
            )
            for f in files
        ]
    )


def map_file_content_response(relative_path: str, content: str) -> FileContentResponse:
    """Map raw file content to HTTP response DTO."""
    return FileContentResponse(path=relative_path, content=content)


def map_list_outputs_response(outputs: list[OutputFileInfo]) -> ListOutputsResponse:
    """Map domain OutputFileInfo list to HTTP response DTO."""
    return ListOutputsResponse(
        outputs=[
            OutputFileItem(
                name=o.name,
                pipeline=o.pipeline,
                path=o.path,
                size=o.size,
            )
            for o in outputs
        ]
    )
