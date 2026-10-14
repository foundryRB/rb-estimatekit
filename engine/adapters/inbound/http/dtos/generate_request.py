"""Request DTO for generation pipelines."""

from __future__ import annotations

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """Body for ``POST /api/projects/{slug}/generate``."""

    pipelines: list[str] | None = None
    """Pipeline names to run. Valid values: ``roadmap``, ``excel``, ``slides``."""

    phase: str | None = None
    """The phase the slide deck sells (for example ``P2``).

    A single-phase project needs none. A project with several phases refuses
    the ``slides`` pipeline without it, listing the phase ids.
    """
