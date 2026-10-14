"""Response DTO for generation pipelines."""

from __future__ import annotations

from pydantic import BaseModel


class GenerateResponse(BaseModel):
    """Response for ``POST /api/projects/{slug}/generate``."""

    results: dict[str, bool]
    success: bool
    phase: str | None = None
    """The phase the slide deck was built for; null when the slides pipeline did not run."""
