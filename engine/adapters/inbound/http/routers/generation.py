"""Routes: generation pipelines."""

from __future__ import annotations

import asyncio
from functools import partial

from fastapi import APIRouter, Depends

from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.dtos.generate_request import GenerateRequest
from engine.adapters.inbound.http.dtos.generate_response import GenerateResponse
from engine.adapters.inbound.http.mappers.generate_mapper import map_generate_response
from engine.container import Container
from engine.domain.model.value_objects.pipeline import Pipeline

router = APIRouter()


@router.post("/{slug}/generate", response_model=GenerateResponse)
async def generate(
    slug: str,
    request: GenerateRequest,
    container: Container = Depends(get_container),  # noqa: B008
) -> GenerateResponse:
    """Run generation pipelines for a project."""
    project_path = container.project_path(slug)
    pipelines = [Pipeline(p) for p in request.pipelines] if request.pipelines else None

    # Run the CPU-bound generation in a thread so we don't block the event loop
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        partial(
            container.generate_all().execute,
            project_path,
            pipelines=pipelines,
            phase=request.phase,
            slides_base_path=f"/projects/{slug}/slides/",
        ),
    )

    return map_generate_response(result)
