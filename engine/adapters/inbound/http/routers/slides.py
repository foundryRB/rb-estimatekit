"""Router: serve built Slidev presentations as static files."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
from starlette.requests import Request
from starlette.responses import RedirectResponse

from engine.adapters.inbound.http.dependencies import get_container

router = APIRouter(tags=["slides"])


@router.get("/projects/{slug}/slides/{file_path:path}")
async def serve_slides(slug: str, file_path: str, request: Request) -> Response:
    """Serve static files from a built Slidev deck."""
    container = get_container()
    project_path = container.project_path(slug)
    dist_dir = (project_path / "output" / "slides" / "dist").resolve()

    if not dist_dir.is_dir():
        return Response("Slides not built yet. Run generation first.", status_code=404)

    resolved = file_path or "index.html"
    target = (dist_dir / resolved).resolve()

    if not target.is_relative_to(dist_dir):
        return Response("Not found", status_code=404)

    if target.is_file():
        return FileResponse(target)

    index = dist_dir / "index.html"
    if index.is_file():
        return FileResponse(index)

    return Response("Not found", status_code=404)


@router.get("/projects/{slug}/slides")
async def slides_redirect(slug: str) -> Response:
    """Redirect to trailing-slash URL so relative paths work."""
    return RedirectResponse(url=f"/projects/{slug}/slides/", status_code=301)
