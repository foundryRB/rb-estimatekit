"""CLI-layer representation of a generation run."""

from __future__ import annotations

from dataclasses import dataclass

from engine.adapters.inbound.cli.dtos.pipeline_result_view import PipelineResultView

__all__ = ["GenerationResultView"]


@dataclass(frozen=True)
class GenerationResultView:
    """Plain CLI-layer representation of a generation run."""

    outcomes: list[PipelineResultView]
    success: bool
    phase: str | None = None
    """The phase the slide deck was built for, when the slides pipeline ran."""
