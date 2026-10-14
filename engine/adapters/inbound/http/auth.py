"""HTTP Basic auth for the engine's inbound HTTP adapter.

EstimateKit has no per-user model: a single shared credential gates it fail-closed,
so a public deployment is never silently open. The gate covers one of two scopes
(ESTIMATEKIT_AUTH_SCOPE): every surface (SPA, /api, /mcp) when the app stands alone,
or only the /mcp machine door when an OIDC reverse proxy (oauth2-proxy) fronts the
human surfaces. Mirrors the protopane/playbook-studio pattern.
"""

from __future__ import annotations

import base64
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import RequestResponseEndpoint

from engine.logging import get_logger

logger = get_logger(__name__)

# The health probe must answer without credentials so liveness/readiness work.
_EXEMPT_PATHS = frozenset({"/api/health"})
_MCP_PREFIX = "/mcp"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _auth_scope() -> str:
    """Which surfaces the Basic gate covers (ESTIMATEKIT_AUTH_SCOPE).

    "all" (default): every surface (SPA, /api, /mcp), the stand-alone posture.
    "mcp": only the /mcp machine door, because an OIDC reverse proxy
    (oauth2-proxy) fronts the SPA and /api for humans, who cannot complete an
    interactive login on a machine-to-machine channel. The chart sets this only
    when that proxy is present, so the human surfaces are never truly open.
    """
    scope = (os.environ.get("ESTIMATEKIT_AUTH_SCOPE") or "all").strip().lower()
    return scope if scope in {"all", "mcp"} else "all"


def _gated(path: str, scope: str) -> bool:
    """Whether a path is subject to the Basic gate under the active scope."""
    if path in _EXEMPT_PATHS:
        return False
    if scope == "mcp":
        return path == _MCP_PREFIX or path.startswith(_MCP_PREFIX + "/")
    return True


def install_auth(app: FastAPI) -> None:
    """Gate the engine's routes behind HTTP Basic auth, fail closed.

    Enforced when ESTIMATEKIT_AUTH_USER and ESTIMATEKIT_AUTH_PASSWORD are both set;
    turned off only by an explicit ESTIMATEKIT_AUTH_DISABLED=true (local dev and
    tests). With neither set, gated routes answer 503: a misconfigured instance is
    closed, never silently open. ESTIMATEKIT_AUTH_SCOPE picks the covered surfaces
    (see _auth_scope); the health endpoint stays exempt so orchestration probes keep
    working.
    """
    user = os.environ.get("ESTIMATEKIT_AUTH_USER", "")
    password = os.environ.get("ESTIMATEKIT_AUTH_PASSWORD", "")
    disabled = _truthy(os.environ.get("ESTIMATEKIT_AUTH_DISABLED"))
    scope = _auth_scope()
    configured = bool(user and password)

    if disabled:
        logger.warning("estimatekit auth is DISABLED; do not expose this instance publicly")
    elif configured:
        logger.info("estimatekit auth is ENABLED (HTTP Basic, scope=%s)", scope)
    else:
        logger.error(
            "estimatekit auth is NOT CONFIGURED: set ESTIMATEKIT_AUTH_USER and "
            "ESTIMATEKIT_AUTH_PASSWORD, or ESTIMATEKIT_AUTH_DISABLED=true for local dev; "
            "gated routes answer 503 until then"
        )

    @app.middleware("http")
    async def _basic_auth(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if disabled or not _gated(request.url.path, scope):
            return await call_next(request)
        if not configured:
            return JSONResponse(
                status_code=503,
                content={"detail": "authentication is not configured"},
            )
        if _is_authorized(request, user, password):
            return await call_next(request)
        return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="estimatekit"'})


def _is_authorized(request: Request, user: str, password: str) -> bool:
    """Constant-time check of an HTTP Basic Authorization header against the configured pair."""
    scheme, _, encoded = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "basic" or not encoded:
        return False
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    got_user, separator, got_password = decoded.partition(":")
    if not separator:
        return False
    user_ok = secrets.compare_digest(got_user, user)
    password_ok = secrets.compare_digest(got_password, password)
    return user_ok and password_ok
