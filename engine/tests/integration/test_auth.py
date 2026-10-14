"""Auth-gate tests for the HTTP adapter (mirrors the protopane pattern).

Verifies the fail-closed HTTP Basic gate installed by
``engine.adapters.inbound.http.auth``. These attest the auth claims in the repo
``intent.yaml`` (INT-ESTIMATEKIT-006..010) via the ``@intent`` decorator from
``pytest_intent``, which the csd-intent audit scans for statically.

``/openapi.json`` stands in for "any gated route": the auth middleware runs
before routing, so it is rejected or admitted purely by the gate, independent of
the business endpoints.
"""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient
from pytest_intent import intent


def _build_client(monkeypatch: pytest.MonkeyPatch, **env: str) -> TestClient:
    """A TestClient over a freshly built app with the given auth env (others cleared)."""
    for key in (
        "ESTIMATEKIT_AUTH_USER",
        "ESTIMATEKIT_AUTH_PASSWORD",
        "ESTIMATEKIT_AUTH_DISABLED",
        "ESTIMATEKIT_AUTH_SCOPE",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from engine.adapters.inbound.http.app import create_app

    return TestClient(create_app())


def _basic(user: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@intent("INT-ESTIMATEKIT-006")
def test_rejects_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """INT-ESTIMATEKIT-006: configured auth refuses an unauthenticated request with 401."""
    client = _build_client(
        monkeypatch, ESTIMATEKIT_AUTH_USER="ops", ESTIMATEKIT_AUTH_PASSWORD="s3cret"
    )
    res = client.get("/openapi.json")
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate", "").lower().startswith("basic")
    # The MCP mount is gated by the same middleware.
    assert client.post("/mcp", json={}).status_code == 401


@intent("INT-ESTIMATEKIT-007")
def test_accepts_valid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """INT-ESTIMATEKIT-007: valid credentials are admitted; a wrong password is refused."""
    client = _build_client(
        monkeypatch, ESTIMATEKIT_AUTH_USER="ops", ESTIMATEKIT_AUTH_PASSWORD="s3cret"
    )
    assert client.get("/openapi.json", headers=_basic("ops", "s3cret")).status_code == 200
    assert client.get("/openapi.json", headers=_basic("ops", "nope")).status_code == 401


@intent("INT-ESTIMATEKIT-008")
def test_health_is_exempt(monkeypatch: pytest.MonkeyPatch) -> None:
    """INT-ESTIMATEKIT-008: the health endpoint answers without credentials (for probes)."""
    client = _build_client(
        monkeypatch, ESTIMATEKIT_AUTH_USER="ops", ESTIMATEKIT_AUTH_PASSWORD="s3cret"
    )
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@intent("INT-ESTIMATEKIT-009")
def test_fails_closed_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """INT-ESTIMATEKIT-009: no credentials and not explicitly disabled -> 503, not open."""
    client = _build_client(monkeypatch)
    assert client.get("/openapi.json").status_code == 503
    assert client.post("/mcp", json={}).status_code == 503
    # Health still answers so probes keep working.
    assert client.get("/api/health").status_code == 200


@intent("INT-ESTIMATEKIT-010")
def test_mcp_scope_gates_only_the_machine_door(monkeypatch: pytest.MonkeyPatch) -> None:
    """INT-ESTIMATEKIT-010: scope=mcp keeps /mcp Basic-gated while the human surfaces
    serve open for an OIDC reverse proxy in front to gate."""
    client = _build_client(
        monkeypatch,
        ESTIMATEKIT_AUTH_USER="ops",
        ESTIMATEKIT_AUTH_PASSWORD="s3cret",
        ESTIMATEKIT_AUTH_SCOPE="mcp",
    )
    # Enter the app lifespan so the /mcp transport's session manager is running: a
    # valid credential follows the /mcp -> /mcp/ redirect into the mount, which would
    # raise "Task group is not initialized" without run(). The gate decision (before
    # routing) is what these assertions exercise.
    with client:
        # The /mcp machine door stays gated: no credential is refused, a valid one admitted.
        assert client.post("/mcp", json={}).status_code == 401
        admitted = client.post("/mcp", json={}, headers=_basic("ops", "s3cret"))
        assert admitted.status_code not in (401, 503)
        # The human surfaces serve open; oauth2-proxy is their gate in front.
        assert client.get("/openapi.json").status_code == 200


@intent("INT-ESTIMATEKIT-010")
def test_mcp_scope_fails_closed_on_the_machine_door(monkeypatch: pytest.MonkeyPatch) -> None:
    """INT-ESTIMATEKIT-010: scope=mcp with no credentials fails the /mcp door closed
    (503) while the human surfaces stay open for the proxy."""
    client = _build_client(monkeypatch, ESTIMATEKIT_AUTH_SCOPE="mcp")
    assert client.post("/mcp", json={}).status_code == 503
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/api/health").status_code == 200


def test_agent_credential_returns_the_basic_pair(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/agent-credential hands the in-app connect menu the base64 HTTP Basic
    pair; behind oauth2-proxy under scope=mcp only an authenticated human reaches it."""
    client = _build_client(
        monkeypatch,
        ESTIMATEKIT_AUTH_USER="ops",
        ESTIMATEKIT_AUTH_PASSWORD="s3cret",
        ESTIMATEKIT_AUTH_SCOPE="mcp",
    )
    res = client.get("/api/agent-credential")
    assert res.status_code == 200
    assert base64.b64decode(res.json()["credential"]).decode() == "ops:s3cret"


def test_agent_credential_fails_closed_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no credential configured there is nothing to hand out: 503, never an
    empty or bogus credential."""
    client = _build_client(monkeypatch, ESTIMATEKIT_AUTH_SCOPE="mcp")
    assert client.get("/api/agent-credential").status_code == 503
