"""Routes: project discovery, scaffolding, and summary."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.dtos.archive_response import ArchiveProjectResponse
from engine.adapters.inbound.http.dtos.delete_response import DeleteProjectResponse
from engine.adapters.inbound.http.dtos.discover_response import DiscoverProjectsResponse
from engine.adapters.inbound.http.dtos.project_summary_response import ProjectSummaryResponse
from engine.adapters.inbound.http.dtos.rename_request import RenameRequest
from engine.adapters.inbound.http.dtos.rename_response import RenameProjectResponse
from engine.adapters.inbound.http.dtos.scaffold_request import ScaffoldRequest
from engine.adapters.inbound.http.dtos.scaffold_response import ScaffoldProjectResponse
from engine.adapters.inbound.http.mappers.archive_mapper import map_archive_response
from engine.adapters.inbound.http.mappers.delete_mapper import map_delete_response
from engine.adapters.inbound.http.mappers.discover_mapper import map_discover_response
from engine.adapters.inbound.http.mappers.project_summary_mapper import (
    map_project_summary_response,
)
from engine.adapters.inbound.http.mappers.rename_mapper import map_rename_response
from engine.adapters.inbound.http.mappers.scaffold_mapper import map_scaffold_response
from engine.container import Container

router = APIRouter()


@router.get("/", response_model=DiscoverProjectsResponse)
async def list_projects(
    container: Container = Depends(get_container),  # noqa: B008
) -> DiscoverProjectsResponse:
    """Discover projects under the server-configured root directory."""
    entries = container.discover_projects().execute(container.projects_root)
    return map_discover_response(entries)


@router.post("/scaffold", response_model=ScaffoldProjectResponse)
async def scaffold_project(
    request: ScaffoldRequest,
    container: Container = Depends(get_container),  # noqa: B008
) -> ScaffoldProjectResponse:
    """Scaffold a new project from templates."""
    # project_path validates the slug via ProjectSlug value object
    container.project_path(request.slug)
    result = container.scaffold_project().execute(
        projects_root=container.projects_root,
        slug=request.slug,
        force=request.force,
    )
    return map_scaffold_response(result)


@router.get("/{slug}/summary", response_model=ProjectSummaryResponse)
async def get_summary(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> ProjectSummaryResponse:
    """Get a lightweight summary of a project."""
    project_path = container.project_path(slug)
    summary = container.get_project_summary().execute(project_path)
    return map_project_summary_response(summary)


@router.delete("/{slug}", response_model=DeleteProjectResponse)
async def delete_project(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> DeleteProjectResponse:
    """Permanently delete a project and all of its data."""
    # project_path validates the slug via ProjectSlug value object
    container.project_path(slug)
    result = container.delete_project().execute(
        projects_root=container.projects_root,
        slug=slug,
    )
    return map_delete_response(result)


@router.post("/{slug}/rename", response_model=RenameProjectResponse)
async def rename_project(
    slug: str,
    request: RenameRequest,
    container: Container = Depends(get_container),  # noqa: B008
) -> RenameProjectResponse:
    """Rename a project's display name and/or slug (the slug rename moves the folder)."""
    # project_path validates the slugs via ProjectSlug value object
    container.project_path(slug)
    if request.new_slug is not None:
        container.project_path(request.new_slug)
    result = container.rename_project().execute(
        projects_root=container.projects_root,
        slug=slug,
        new_slug=request.new_slug,
        new_name=request.new_name,
    )
    return map_rename_response(slug, result)


@router.post("/{slug}/archive", response_model=ArchiveProjectResponse)
async def archive_project(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> ArchiveProjectResponse:
    """Archive a project: keep all data, drop it from the active listing."""
    # project_path validates the slug via ProjectSlug value object
    container.project_path(slug)
    result = container.archive_project().execute(
        projects_root=container.projects_root,
        slug=slug,
    )
    return map_archive_response(result, archived=True)


@router.post("/{slug}/unarchive", response_model=ArchiveProjectResponse)
async def unarchive_project(
    slug: str,
    container: Container = Depends(get_container),  # noqa: B008
) -> ArchiveProjectResponse:
    """Unarchive a project, returning it to the active listing."""
    # project_path validates the slug via ProjectSlug value object
    container.project_path(slug)
    result = container.unarchive_project().execute(
        projects_root=container.projects_root,
        slug=slug,
    )
    return map_archive_response(result, archived=False)
