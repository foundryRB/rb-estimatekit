"""CLI-layer representation of a single pipeline outcome."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["PipelineResultView"]


@dataclass(frozen=True)
class PipelineResultView:
    """Plain CLI-layer representation of a single pipeline result."""

    name: str
    success: bool
