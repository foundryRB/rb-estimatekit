"""Mapper for phase-minting responses."""

from __future__ import annotations

from engine.adapters.inbound.http.dtos.scaffold_phase_response import ScaffoldPhaseResponse


def map_scaffold_phase_response(
    slug: str, phase_id: str, files: list[str],
) -> ScaffoldPhaseResponse:
    """Map the minted phase's written paths to the response DTO."""
    return ScaffoldPhaseResponse(slug=slug, phase_id=phase_id, files=list(files))
