"""Inbound port: generate all outputs for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.generation_result import GenerationResult
from engine.domain.model.value_objects.pipeline import Pipeline

__all__ = ["GenerateAllPort"]


@runtime_checkable
class GenerateAllPort(Protocol):
    """Orchestrate full generation pipeline — roadmap, excels, slides."""

    def execute(
        self,
        project_path: Path,
        *,
        pipelines: list[Pipeline] | None = None,
        phase: str | None = None,
        slides_base_path: str = "/",
    ) -> GenerationResult:
        """Run selected generation pipelines.

        *phase* names the phase the slide deck sells. A single-phase project
        needs none; a multi-phase project refuses the slides pipeline without it.
        """
        ...
