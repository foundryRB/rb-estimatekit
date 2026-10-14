"""Routes: phases (mint a new phase in an existing project)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.dtos.scaffold_phase_request import ScaffoldPhaseRequest
from engine.adapters.inbound.http.dtos.scaffold_phase_response import ScaffoldPhaseResponse
from engine.adapters.inbound.http.mappers.phase_mapper import map_scaffold_phase_response
from engine.container import Container

router = APIRouter()


@router.post("/{slug}/phases/{phase_id}", response_model=ScaffoldPhaseResponse)
async def scaffold_phase(
    slug: str,
    phase_id: str,
    request: ScaffoldPhaseRequest | None = None,
    container: Container = Depends(get_container),  # noqa: B008
) -> ScaffoldPhaseResponse:
    """Mint a phase: its phase-table row, its matrix column and its example-marked file set."""
    project_path = container.project_path(slug)
    force = request.force if request is not None else False
    files = container.scaffold_phase().execute(project_path, phase_id, force=force)
    return map_scaffold_phase_response(slug, phase_id, files)
