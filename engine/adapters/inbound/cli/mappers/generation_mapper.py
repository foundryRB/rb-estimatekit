"""Mapper: domain GenerationResult to CLI GenerationResultView."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.adapters.inbound.cli.dtos.generation_result_view import GenerationResultView
from engine.adapters.inbound.cli.dtos.pipeline_result_view import PipelineResultView

if TYPE_CHECKING:
    from engine.domain.model.value_objects.generation_result import GenerationResult


def map_generation_result(result: GenerationResult) -> GenerationResultView:
    """Map a domain GenerationResult to a CLI GenerationResultView."""
    return GenerationResultView(
        outcomes=[
            PipelineResultView(name=pipeline.value, success=success)
            for pipeline, success in result.outcomes.items()
        ],
        success=result.success,
        phase=result.phase,
    )
