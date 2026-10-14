"""Routes: project file browsing, editing, output listing, and zip export/import."""

from __future__ import annotations

import io
import mimetypes
import zipfile

from fastapi import APIRouter, Depends, UploadFile
from fastapi import File as FastAPIFile
from fastapi.responses import FileResponse, StreamingResponse

from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.dtos.file_content_response import FileContentResponse
from engine.adapters.inbound.http.dtos.list_files_response import ListFilesResponse
from engine.adapters.inbound.http.dtos.list_outputs_response import ListOutputsResponse
from engine.adapters.inbound.http.dtos.save_file_request import SaveFileRequest
from engine.adapters.inbound.http.mappers.files_mapper import (
    map_file_content_response,
    map_list_files_response,
    map_list_outputs_response,
)
from engine.container import Container

router = APIRouter()


@router.get("/{slug}/files", response_model=ListFilesResponse)
async def list_files(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> ListFilesResponse:
    """List all editable data files in a project."""
    project_path = container.project_path(slug)
    files = container.list_project_files().execute(project_path)
    return map_list_files_response(files)


@router.get("/{slug}/files/{file_path:path}", response_model=FileContentResponse)
async def read_file(
    slug: str,
    file_path: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> FileContentResponse:
    """Read the raw content of a single project file."""
    project_path = container.project_path(slug)
    content = container.read_project_file().execute(project_path, file_path)
    return map_file_content_response(file_path, content)


@router.put("/{slug}/files/{file_path:path}", status_code=204)
async def save_file(
    slug: str,
    file_path: str,
    request: SaveFileRequest,
    container: Container = Depends(get_container),  # noqa: B008
) -> None:
    """Write content to a project file (create or overwrite)."""
    project_path = container.project_path(slug)
    container.write_project_file().execute(project_path, file_path, request.content)


@router.delete("/{slug}/files/{file_path:path}", status_code=204)
async def delete_file(
    slug: str,
    file_path: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> None:
    """Delete a project data file (e.g. to drop scaffolded files a project no longer needs)."""
    project_path = container.project_path(slug)
    container.delete_project_file().execute(project_path, file_path)


@router.get("/{slug}/outputs", response_model=ListOutputsResponse)
async def list_outputs(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> ListOutputsResponse:
    """List all generated output files for a project."""
    project_path = container.project_path(slug)
    outputs = container.list_output_files().execute(project_path)
    return map_list_outputs_response(outputs)


@router.get("/{slug}/outputs/{file_path:path}")
async def download_output(
    slug: str,
    file_path: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> FileResponse:
    """Download a single generated output file."""
    project_path = container.project_path(slug)
    target = container.download_output_file().execute(project_path, file_path)

    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return FileResponse(
        path=target,
        filename=target.name,
        media_type=media_type,
    )


@router.get("/{slug}/export")
async def export_project(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> StreamingResponse:
    """Export all project data files as a ZIP archive."""
    project_path = container.project_path(slug)
    entries = container.export_project().execute(project_path)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            zf.writestr(entry.path, entry.content)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{slug}.zip"'},
    )


@router.post("/{slug}/import", status_code=204)
async def import_project(
    slug: str,
    file: UploadFile = FastAPIFile(...),  # noqa: B008
    container: Container = Depends(get_container),  # noqa: B008
) -> None:
    """Import project data files from a ZIP archive (overwrites existing)."""
    project_path = container.project_path(slug)

    data = await file.read()
    buf = io.BytesIO(data)

    files: dict[str, bytes] = {}
    with zipfile.ZipFile(buf, "r") as zf:
        for member in zf.infolist():
            if not member.is_dir():
                files[member.filename] = zf.read(member.filename)

    container.import_project().execute(project_path, files)

