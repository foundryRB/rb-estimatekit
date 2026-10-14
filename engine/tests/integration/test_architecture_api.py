"""Integration tests for the architecture diagram routes.

The renderer is faked at the adapter seam (monkeypatching PlantUmlRenderer)
so the suite stays green on machines without a JRE. The real subprocess
adapter is covered by test_plantuml_renderer.py, which skips when java or
the pinned jar is absent - the runtime image ships both.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_intent import intent

import engine.adapters.inbound.http.dependencies as deps
from engine.adapters.inbound.http.app import create_app
from engine.adapters.outbound.plantuml.plantuml_renderer import PlantUmlRenderer
from engine.domain.exceptions import DiagramRenderError

FAKE_SVG = '<svg xmlns="http://www.w3.org/2000/svg"><!-- fake --></svg>'


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _set_projects_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """Point the server's projects root at a temp directory for every test."""
    monkeypatch.setenv("ESTIMATEKIT_PROJECTS_ROOT", str(tmp_path))
    deps.get_container.cache_clear()
    yield
    deps.get_container.cache_clear()


@pytest.fixture()
def fake_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the subprocess renderer with a canned SVG document."""
    monkeypatch.setattr(PlantUmlRenderer, "render_svg", lambda self, source: FAKE_SVG)


@pytest.fixture()
def failing_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the subprocess renderer with one that always fails."""

    def _fail(self: PlantUmlRenderer, source: str) -> str:
        raise DiagramRenderError("Syntax Error on line 1")

    monkeypatch.setattr(PlantUmlRenderer, "render_svg", _fail)


@pytest.fixture()
def client() -> TestClient:
    """Provide a fresh TestClient per test - no server process needed."""
    return TestClient(create_app())


@pytest.fixture()
def scaffolded_project(client: TestClient) -> str:
    """Scaffold a project (ships P1-overview.puml + P2-overview.puml)."""
    slug = "arch-project"
    resp = client.post("/api/projects/scaffold", json={"slug": slug})
    assert resp.status_code == 200, resp.text
    return slug


# ── Diagrams ──────────────────────────────────────────────────


class TestArchitectureDiagrams:
    """GET /api/projects/{slug}/architecture/diagrams[/{name}]"""

    @intent("INT-ESTIMATEKIT-015")
    def test_list_returns_only_the_puml_sources(
        self, client: TestClient, scaffolded_project: str
    ) -> None:
        """INT-ESTIMATEKIT-015: the listing names exactly the project's .puml
        sources under data/architecture/ - the TSVs that share the folder are
        not diagrams."""
        resp = client.get(f"/api/projects/{scaffolded_project}/architecture/diagrams")
        assert resp.status_code == 200, resp.text
        diagrams = resp.json()["diagrams"]
        names = [d["name"] for d in diagrams]
        assert "P1-overview.puml" in names
        assert all(n.endswith(".puml") for n in names)
        assert all(d["path"].startswith("data/architecture/") for d in diagrams)

    def test_list_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/projects/does-not-exist/architecture/diagrams")
        assert resp.status_code == 404

    @intent("INT-ESTIMATEKIT-015")
    def test_render_returns_name_and_svg(
        self, client: TestClient, scaffolded_project: str, fake_renderer: None
    ) -> None:
        """INT-ESTIMATEKIT-015: a diagram fetch answers {name, svg}, produced
        by the engine's own renderer port - no external service involved."""
        resp = client.get(
            f"/api/projects/{scaffolded_project}/architecture/diagrams/P1-overview.puml"
        )
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"name": "P1-overview.puml", "svg": FAKE_SVG}

    def test_render_accepts_the_bare_diagram_name(
        self, client: TestClient, scaffolded_project: str, fake_renderer: None
    ) -> None:
        resp = client.get(
            f"/api/projects/{scaffolded_project}/architecture/diagrams/P1-overview"
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["svg"] == FAKE_SVG

    @intent("INT-ESTIMATEKIT-015")
    def test_render_unknown_diagram_returns_404(
        self, client: TestClient, scaffolded_project: str, fake_renderer: None
    ) -> None:
        """INT-ESTIMATEKIT-015: an unknown diagram answers the API's 404 idiom."""
        resp = client.get(
            f"/api/projects/{scaffolded_project}/architecture/diagrams/no-such-diagram"
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_render_missing_project_returns_404(
        self, client: TestClient, fake_renderer: None
    ) -> None:
        resp = client.get("/api/projects/does-not-exist/architecture/diagrams/P1-overview")
        assert resp.status_code == 404

    @intent("INT-ESTIMATEKIT-015")
    def test_render_failure_returns_422_with_the_reason(
        self, client: TestClient, scaffolded_project: str, failing_renderer: None
    ) -> None:
        """INT-ESTIMATEKIT-015: a render failure surfaces 422 and carries the
        renderer's reason instead of a blank error."""
        resp = client.get(
            f"/api/projects/{scaffolded_project}/architecture/diagrams/P1-overview"
        )
        assert resp.status_code == 422
        assert "Syntax Error on line 1" in resp.json()["detail"]

    def test_render_rejects_a_name_with_path_separators(
        self, client: TestClient, scaffolded_project: str, fake_renderer: None
    ) -> None:
        """A name is a bare filename; an encoded traversal never resolves
        outside the architecture folder."""
        resp = client.get(
            f"/api/projects/{scaffolded_project}/architecture/diagrams/..%2F..%2Fproject.yaml"
        )
        assert resp.status_code in (400, 404)
