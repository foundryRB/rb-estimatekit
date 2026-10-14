"""ExecutiveSummaryData — structured content for the executive summary slide."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ExecutiveSummaryData"]


@dataclass
class ExecutiveSummaryData:
    """Structured content for the executive summary slide.

    Loaded from Slide-ExecutiveSummary.tsv.
    """

    context_description: str = ""
    context_bullets: list[str] = field(default_factory=list)
    rationale: list[tuple[str, str]] = field(default_factory=list)   # key-value pairs
    highlights: list[tuple[str, str]] = field(default_factory=list)  # key-value pairs
