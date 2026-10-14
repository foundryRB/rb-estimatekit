"""FastAPI application factory."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response
from mcp.server.fastmcp import FastMCP

from engine.adapters.inbound.http.auth import install_auth
from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.exception_handlers import register_exception_handler
from engine.adapters.inbound.http.routers import (
    architecture,
    audit,
    files,
    generation,
    guide,
    phases,
    projects,
    slides,
    system,
)
from engine.adapters.inbound.mcp.server import build_mcp_server

_FRONTEND_DIST_ENV = "ESTIMATEKIT_FRONTEND_DIST"


def _frontend_dir() -> Path:
    """The built web SPA, placed at <repo>/web/dist in the runtime image
    (devops/Dockerfile). Mounted only when present, so the native dev path
    (Vite serves the SPA and proxies /api here) and the test suite are
    unaffected. Mirrors night-approver / protopane.
    $ESTIMATEKIT_FRONTEND_DIST overrides the location.
    """
    env = os.environ.get(_FRONTEND_DIST_ENV)
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[4] / "web" / "dist"


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    mcp_server = build_mcp_server(get_container())
    app = FastAPI(
        title="EstimateKit Engine",
        description="Project estimation engine — hexagonal backend",
        version="0.1.0",
        lifespan=_lifespan(mcp_server),
    )

    # Gate the whole app (SPA + API + /mcp) behind fail-closed HTTP Basic auth,
    # except /api/health. Disabled in dev/tests via ESTIMATEKIT_AUTH_DISABLED=true.
    install_auth(app)

    register_exception_handler(app)

    app.include_router(system.router, prefix="/api", tags=["system"])
    app.include_router(guide.router, prefix="/api", tags=["guide"])
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(phases.router, prefix="/api/projects", tags=["phases"])
    app.include_router(generation.router, prefix="/api/projects", tags=["generation"])
    app.include_router(files.router, prefix="/api/projects", tags=["files"])
    app.include_router(architecture.router, prefix="/api/projects", tags=["architecture"])
    app.include_router(audit.router, prefix="/api/projects", tags=["audit"])
    app.include_router(slides.router)

    # The MCP transport lives under /mcp/. The bare path must work too (clients
    # connect to https://<host>/mcp), and it cannot rely on the router's implicit
    # slash redirect: the SPA mount at / matches /mcp first and answers 405. An
    # explicit 307 keeps the method and body.
    @app.api_route("/mcp", methods=["GET", "POST", "DELETE"], include_in_schema=False)
    async def _mcp_redirect() -> RedirectResponse:
        return RedirectResponse(url="/mcp/", status_code=307)

    app.mount("/mcp", mcp_server.streamable_http_app())

    # Serve the built SPA. Registered after the API routers and the /mcp mount so
    # those win; /api paths stay JSON 404s and are never swallowed by the catch-all.
    # A direct hit to a client-side route (e.g. /projects/<slug>) falls back to
    # index.html so the SPA boots and routes in-browser instead of a bare 404.
    # Skipped when web/dist is absent (native dev: Vite serves the SPA and proxies
    # /api here; and tests).
    frontend = _frontend_dir()
    if frontend.is_dir():
        root = frontend.resolve()

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> Response:
            if full_path == "api" or full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not Found")
            candidate = (frontend / full_path).resolve()
            if full_path and candidate.is_file() and root in candidate.parents:
                return FileResponse(str(candidate))
            return FileResponse(str(frontend / "index.html"))

    return app


def _lifespan(mcp_server: FastMCP) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Run the MCP session manager for the app's lifetime."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp_server.session_manager.run():
            yield

    return lifespan
