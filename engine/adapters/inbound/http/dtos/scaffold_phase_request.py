"""Request DTO for minting a phase."""

from __future__ import annotations

from pydantic import BaseModel


class ScaffoldPhaseRequest(BaseModel):
    """Body for ``POST /api/projects/{slug}/phases/{phase_id}``."""

    force: bool = False
    """Overwrite the phase's existing files with the example set."""
