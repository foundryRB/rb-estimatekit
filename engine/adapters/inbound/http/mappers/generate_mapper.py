"""Mapper for generation responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.adapters.inbound.http.dtos.generate_response import GenerateResponse

if TYPE_CHECKING:
    from engine.domain.model.value_objects.generation_result import GenerationResult


def map_generate_response(result: GenerationResult) -> GenerateResponse:
    """Map a domain GenerationResult to the response DTO."""
    return GenerateResponse(
        results={pipeline.value: success for pipeline, success in result.outcomes.items()},
        success=result.success,
        phase=result.phase,
    )
