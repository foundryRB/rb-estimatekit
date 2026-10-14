"""Routes: guide — static getting-started content."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from engine.adapters.inbound.http.dependencies import get_container
from engine.container import Container

router = APIRouter()


@router.get("/guide")
async def get_guide(
    container: Container = Depends(get_container),  # noqa: B008
) -> dict[str, Any]:
    return container.read_guide()
