"""Integration tests for the FastAPI HTTP adapter.

These tests use FastAPI's TestClient (backed by httpx) to exercise every
API endpoint *without* starting a real server. They catch wiring, routing,
and serialisation problems the same way a browser would — but run in CI
with ``python -m pytest``.

The projects root is configured via the ``ESTIMATEKIT_PROJECTS_ROOT``
environment variable, which each test points at a fresh ``tmp_path``.

Requires:  pip install -e ".[http,dev]"
"""

from __future__ import annotations

import re
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_intent import intent

import engine.adapters.inbound.http.dependencies as deps
from engine.adapters.inbound.http.app import create_app

# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _set_projects_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """Point the server's projects root at a temp directory for every test.

    We set the env var *and* clear the Container lru_cache so that
    ``get_container()`` creates a fresh Container that re-resolves
    the projects root from the new env value.
    """
    monkeypatch.setenv("ESTIMATEKIT_PROJECTS_ROOT", str(tmp_path))
    deps.get_container.cache_clear()
    yield
    deps.get_container.cache_clear()


@pytest.fixture()
def projects_root(tmp_path: Path) -> Path:
    """Convenience accessor — matches the path _set_projects_root uses."""
    return tmp_path


@pytest.fixture(autouse=True)
def _skip_slidev_build(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent the slow ``npx slidev build`` step from running in tests."""
    from engine.adapters.outbound.slidev.slidev_builder import SlidevBuilder

    monkeypatch.setattr(SlidevBuilder, "build", lambda self, *a, **kw: True)


@pytest.fixture()
def client() -> TestClient:
    """Provide a fresh TestClient per test — no server process needed."""
    app = create_app()
    return TestClient(app)


@pytest.fixture()
def scaffolded_project(client: TestClient) -> str:
    """Scaffold a project and return its slug (reusable across tests)."""
    slug = "test-project"
    resp = client.post(
        "/api/projects/scaffold",
        json={"slug": slug},
    )
    assert resp.status_code == 200, resp.text
    return slug


# ── Health ────────────────────────────────────────────────────


class TestHealth:
    """GET /api/health — the first thing the frontend calls on mount."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "estimatekit-engine"

    def test_health_content_type_is_json(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert "application/json" in resp.headers["content-type"]

    def test_health_reports_the_running_image_tag(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The chart injects the promoted tag as $APP_VERSION, and the OIDC gate
        skips this route, so an external observer can read which release serves
        without a credential. A constant in code would not be freshness."""
        monkeypatch.setenv("APP_VERSION", "2.5.1")
        assert client.get("/api/health").json()["version"] == "2.5.1"

    def test_health_answers_without_an_injected_tag(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("APP_VERSION", raising=False)
        assert client.get("/api/health").json()["version"] == "dev"


# ── Project Discovery ────────────────────────────────────────


class TestDiscoverProjects:
    """GET /api/projects/"""

    def test_discover_empty_root(self, client: TestClient) -> None:
        resp = client.get("/api/projects/")
        assert resp.status_code == 200
        assert resp.json()["projects"] == []

    def test_discover_after_scaffold(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.get("/api/projects/")
        assert resp.status_code == 200
        slugs = resp.json()["projects"]
        assert scaffolded_project in slugs


# ── Scaffold ──────────────────────────────────────────────────


class TestScaffoldProject:
    """POST /api/projects/scaffold"""

    def test_scaffold_creates_project_dir(
        self, client: TestClient, projects_root: Path
    ) -> None:
        slug = "new-proj"
        resp = client.post(
            "/api/projects/scaffold",
            json={"slug": slug},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == slug
        assert (projects_root / slug).is_dir()

    def test_scaffold_duplicate_without_force_fails(
        self, client: TestClient
    ) -> None:
        payload = {"slug": "dup-test"}
        resp1 = client.post("/api/projects/scaffold", json=payload)
        assert resp1.status_code == 200

        resp2 = client.post("/api/projects/scaffold", json=payload)
        assert resp2.status_code == 409  # ProjectAlreadyExistsError → 409 Conflict

    def test_scaffold_missing_slug_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/projects/scaffold",
            json={},
        )
        assert resp.status_code == 422  # Pydantic validation error

    def test_scaffold_invalid_slug_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/api/projects/scaffold",
            json={"slug": "../evil"},
        )
        assert resp.status_code == 400


# ── Delete ────────────────────────────────────────────────────


class TestDeleteProject:
    """DELETE /api/projects/{slug}"""

    def test_delete_removes_project_dir(
        self, client: TestClient, projects_root: Path, scaffolded_project: str
    ) -> None:
        assert (projects_root / scaffolded_project).is_dir()
        resp = client.delete(f"/api/projects/{scaffolded_project}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["slug"] == scaffolded_project
        assert body["deleted"] is True
        assert not (projects_root / scaffolded_project).exists()

    def test_delete_drops_it_from_discovery(
        self, client: TestClient, scaffolded_project: str
    ) -> None:
        client.delete(f"/api/projects/{scaffolded_project}")
        resp = client.get("/api/projects/")
        assert scaffolded_project not in resp.json()["projects"]

    def test_delete_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/projects/does-not-exist")
        assert resp.status_code == 404

    def test_delete_invalid_slug_returns_400(self, client: TestClient) -> None:
        # "bad.name" is a single clean path segment but fails ProjectSlug
        # validation ('.' is not allowed), so the slug guard rejects it
        # before any filesystem access.
        resp = client.delete("/api/projects/bad.name")
        assert resp.status_code == 400


# ── Rename ────────────────────────────────────────────────────


class TestRenameProject:
    """POST /api/projects/{slug}/rename"""

    @intent("INT-ESTIMATEKIT-013")
    def test_rename_slug_moves_the_project(
        self, client: TestClient, projects_root: Path, scaffolded_project: str
    ) -> None:
        """INT-ESTIMATEKIT-013: after a slug rename the project answers only
        under the new slug — the directory moved, the old slug is gone from
        discovery, and the new slug serves the same data."""
        resp = client.post(
            f"/api/projects/{scaffolded_project}/rename",
            json={"new_slug": "renamed-project"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["slug"] == scaffolded_project
        assert body["new_slug"] == "renamed-project"
        assert body["renamed"] is True
        assert not (projects_root / scaffolded_project).exists()
        assert (projects_root / "renamed-project" / "project.yaml").is_file()

        listing = client.get("/api/projects/").json()
        assert scaffolded_project not in listing["projects"]
        assert "renamed-project" in listing["projects"]
        assert client.get(f"/api/projects/{scaffolded_project}/summary").status_code == 404
        assert client.get("/api/projects/renamed-project/summary").status_code == 200

    def test_rename_display_name_only_keeps_the_slug(
        self, client: TestClient, projects_root: Path, scaffolded_project: str
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/rename",
            json={"new_name": "Fresh Display Name"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["new_slug"] == scaffolded_project
        assert (projects_root / scaffolded_project).is_dir()
        summary = client.get(f"/api/projects/{scaffolded_project}/summary").json()
        assert summary["name"] == "Fresh Display Name"

    def test_rename_slug_and_name_together(
        self, client: TestClient, scaffolded_project: str
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/rename",
            json={"new_slug": "both-renamed", "new_name": "Both Renamed"},
        )
        assert resp.status_code == 200, resp.text
        summary = client.get("/api/projects/both-renamed/summary").json()
        assert summary["name"] == "Both Renamed"

    @intent("INT-ESTIMATEKIT-013")
    def test_rename_to_occupied_slug_is_refused_with_the_reason(
        self, client: TestClient, projects_root: Path, scaffolded_project: str
    ) -> None:
        """INT-ESTIMATEKIT-013: an occupied target slug is refused (409) and
        both projects are left untouched."""
        client.post("/api/projects/scaffold", json={"slug": "occupied"})
        resp = client.post(
            f"/api/projects/{scaffolded_project}/rename",
            json={"new_slug": "occupied"},
        )
        assert resp.status_code == 409
        assert "exists" in resp.json()["detail"]
        assert (projects_root / scaffolded_project / "project.yaml").is_file()
        assert (projects_root / "occupied" / "project.yaml").is_file()

    @intent("INT-ESTIMATEKIT-013")
    def test_rename_to_malformed_slug_is_refused_with_the_reason(
        self, client: TestClient, projects_root: Path, scaffolded_project: str
    ) -> None:
        """INT-ESTIMATEKIT-013: a malformed target slug is refused (400)
        before anything moves."""
        resp = client.post(
            f"/api/projects/{scaffolded_project}/rename",
            json={"new_slug": "../evil"},
        )
        assert resp.status_code == 400
        assert "slug" in resp.json()["detail"].lower()
        assert (projects_root / scaffolded_project / "project.yaml").is_file()

    def test_rename_without_any_target_returns_400(
        self, client: TestClient, scaffolded_project: str
    ) -> None:
        resp = client.post(f"/api/projects/{scaffolded_project}/rename", json={})
        assert resp.status_code == 400

    def test_rename_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/projects/does-not-exist/rename",
            json={"new_slug": "anywhere"},
        )
        assert resp.status_code == 404


# ── Archive / Unarchive ──────────────────────────────────────


class TestArchiveLifecycle:
    """POST /api/projects/{slug}/archive and /unarchive"""

    @intent("INT-ESTIMATEKIT-014")
    def test_archive_parks_the_project_visibly(
        self, client: TestClient, projects_root: Path, scaffolded_project: str
    ) -> None:
        """INT-ESTIMATEKIT-014: an archived project keeps its data, drops out
        of the active listing, and stays visible in the archived listing."""
        resp = client.post(f"/api/projects/{scaffolded_project}/archive")
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"slug": scaffolded_project, "archived": True}

        listing = client.get("/api/projects/").json()
        assert scaffolded_project not in listing["projects"]
        assert scaffolded_project in listing["archived"]

        # Every byte of project data is still there and still served.
        assert (projects_root / scaffolded_project / "project.yaml").is_file()
        summary = client.get(f"/api/projects/{scaffolded_project}/summary")
        assert summary.status_code == 200
        assert summary.json()["archived"] is True

    @intent("INT-ESTIMATEKIT-014")
    def test_unarchive_returns_it_to_the_active_listing(
        self, client: TestClient, scaffolded_project: str
    ) -> None:
        """INT-ESTIMATEKIT-014: unarchiving returns the project unchanged."""
        client.post(f"/api/projects/{scaffolded_project}/archive")
        resp = client.post(f"/api/projects/{scaffolded_project}/unarchive")
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"slug": scaffolded_project, "archived": False}

        listing = client.get("/api/projects/").json()
        assert scaffolded_project in listing["projects"]
        assert scaffolded_project not in listing["archived"]
        summary = client.get(f"/api/projects/{scaffolded_project}/summary").json()
        assert summary["archived"] is False

    def test_archive_is_idempotent(
        self, client: TestClient, scaffolded_project: str
    ) -> None:
        client.post(f"/api/projects/{scaffolded_project}/archive")
        resp = client.post(f"/api/projects/{scaffolded_project}/archive")
        assert resp.status_code == 200
        assert resp.json()["archived"] is True

    def test_archive_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/projects/does-not-exist/archive")
        assert resp.status_code == 404

    def test_unarchive_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/projects/does-not-exist/unarchive")
        assert resp.status_code == 404


# ── Project Summary ──────────────────────────────────────────


class TestProjectSummary:
    """GET /api/projects/{slug}/summary"""

    def test_summary_of_scaffolded_project(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.get(f"/api/projects/{scaffolded_project}/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert "name" in body
        assert "client" in body
        assert "phase_count" in body

    def test_summary_of_missing_project_fails(self, client: TestClient) -> None:
        resp = client.get("/api/projects/does-not-exist/summary")
        assert resp.status_code == 404


# ── File Listing ──────────────────────────────────────────────


class TestListFiles:
    """GET /api/projects/{slug}/files"""

    def test_list_files_of_scaffolded_project(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.get(f"/api/projects/{scaffolded_project}/files")
        assert resp.status_code == 200
        body = resp.json()
        assert "files" in body
        assert isinstance(body["files"], list)

    def test_list_files_missing_project_fails(self, client: TestClient) -> None:
        resp = client.get("/api/projects/nonexistent/files")
        assert resp.status_code == 404


# ── File Read / Write ────────────────────────────────────────


class TestFileReadWrite:
    """GET/PUT /api/projects/{slug}/files/{path}"""

    def test_read_project_yaml(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.get(
            f"/api/projects/{scaffolded_project}/files/project.yaml",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "content" in body

    def test_write_and_read_back(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        file_path = "data/slides/test-notes.tsv"
        content = "Col1\tCol2\nA\tB\n"

        # Write
        put_resp = client.put(
            f"/api/projects/{scaffolded_project}/files/{file_path}",
            json={"content": content},
        )
        assert put_resp.status_code == 204

        # Read back
        get_resp = client.get(
            f"/api/projects/{scaffolded_project}/files/{file_path}",
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["content"] == content

    def test_delete_removes_the_file(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        file_path = "data/slides/scratch.tsv"
        client.put(
            f"/api/projects/{scaffolded_project}/files/{file_path}",
            json={"content": "Col1\tCol2\nA\tB\n"},
        )

        del_resp = client.delete(
            f"/api/projects/{scaffolded_project}/files/{file_path}",
        )
        assert del_resp.status_code == 204

        # Gone: a subsequent read is a 404.
        get_resp = client.get(
            f"/api/projects/{scaffolded_project}/files/{file_path}",
        )
        assert get_resp.status_code == 404

    def test_delete_missing_file_returns_404(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.delete(
            f"/api/projects/{scaffolded_project}/files/data/slides/nope.tsv",
        )
        assert resp.status_code == 404

    def test_delete_escaping_path_returns_400(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.delete(
            f"/api/projects/{scaffolded_project}/files/../../evil.tsv",
        )
        assert resp.status_code == 400


# ── Output Listing ────────────────────────────────────────────


class TestListOutputs:
    """GET /api/projects/{slug}/outputs"""

    def test_outputs_empty_for_new_project(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.get(f"/api/projects/{scaffolded_project}/outputs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["outputs"] == []


# ── Audit ─────────────────────────────────────────────────────


class TestAudit:
    """POST /api/projects/{slug}/audit"""

    @intent("INT-ESTIMATEKIT-005")
    def test_audit_scaffolded_project_returns_200(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        """INT-ESTIMATEKIT-005: running a project's audit executes the standalone
        auditor suite and reports a structured pass/fail per check (a list of
        check items plus passed/failed/skipped counts and an overall ``passed``).
        """
        resp = client.post(f"/api/projects/{scaffolded_project}/audit")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Verify response shape
        assert "checks" in body
        assert isinstance(body["checks"], list)
        assert "passed_count" in body
        assert "failed_count" in body
        assert "skipped_count" in body
        assert "passed" in body
        assert "duration_ms" in body
        # Counts should be consistent
        total = body["passed_count"] + body["failed_count"] + body["skipped_count"]
        assert total == len(body["checks"])

    def test_audit_scaffolded_project_fails_only_scaffold_checks(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        """The example template data is internally consistent: the only audit
        failures on a fresh scaffold are the scaffold-sentinel checks, which
        enumerate exactly the example content still to be authored."""
        resp = client.post(f"/api/projects/{scaffolded_project}/audit")
        assert resp.status_code == 200
        body = resp.json()
        failed = [c for c in body["checks"] if c["outcome"] == "failed"]
        assert failed, "a fresh scaffold must fail its sentinel checks"
        assert body["passed"] is False
        non_scaffold = [c for c in failed if c["category"] != "scaffold"]
        assert non_scaffold == [], (
            "Non-sentinel audit failures on a fresh scaffold:\n"
            + "\n".join(
                f"  [{c['category']}] {c['name']}: {c['message']}"
                for c in non_scaffold
            )
        )

    def test_audit_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/projects/nonexistent/audit")
        assert resp.status_code == 404

    def test_audit_check_items_have_expected_fields(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(f"/api/projects/{scaffolded_project}/audit")
        assert resp.status_code == 200
        checks = resp.json()["checks"]
        if checks:
            item = checks[0]
            assert "node_id" in item
            assert "name" in item
            assert "category" in item
            assert "outcome" in item
            assert item["outcome"] in ("passed", "failed", "skipped")
            assert "message" in item

    def test_audit_returns_advisory_suggestions_without_failing(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        """INT-ESTIMATEKIT-011: the scaffold ships design lead 0 and testing lag
        0, so the audit raises those advisory suggestions — and they never
        change pass/fail: the only failed checks are the sentinel gates, never
        a suggestion."""
        resp = client.post(f"/api/projects/{scaffolded_project}/audit")
        assert resp.status_code == 200
        body = resp.json()
        failed_categories = {
            c["category"] for c in body["checks"] if c["outcome"] == "failed"
        }
        assert failed_categories <= {"scaffold"}
        codes = {s["code"] for s in body["suggestions"]}
        assert {"zero-design-lead", "zero-testing-lag"} <= codes
        for s in body["suggestions"]:
            assert {"code", "title", "detail", "category", "severity"} <= s.keys()
            assert s["severity"] == "warning"


# ── Generate ──────────────────────────────────────────────────


class TestGenerate:
    """POST /api/projects/{slug}/generate"""

    def test_generate_scaffolded_project_returns_200(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/generate",
            json={"pipelines": ["roadmap"]},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "results" in body
        assert "success" in body
        assert isinstance(body["results"], dict)
        assert body["results"].get("roadmap") is True
        assert body["success"] is True

    def test_generate_all_pipelines(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/generate",
            json={"phase": "P1"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        # All three pipeline keys should be present
        assert "roadmap" in body["results"]
        assert "excel" in body["results"]
        assert "slides" in body["results"]
        assert body["phase"] == "P1"

    @intent("INT-ESTIMATEKIT-017")
    def test_generate_slides_on_a_multi_phase_project_needs_the_phase(
        self,
        client: TestClient,
        scaffolded_project: str,
        projects_root: Path,
    ) -> None:
        """The scaffold defines two phases, so an unnamed deck is refused before writing."""
        resp = client.post(f"/api/projects/{scaffolded_project}/generate", json={})
        assert resp.status_code == 422, resp.text
        assert "P1, P2" in resp.json()["detail"]
        assert not (projects_root / scaffolded_project / "output" / "roadmap").exists()

    def test_generate_without_slides_needs_no_phase(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/generate",
            json={"pipelines": ["roadmap", "excel"]},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["phase"] is None

    def test_generate_unknown_phase_returns_422(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/generate",
            json={"phase": "P9"},
        )
        assert resp.status_code == 422, resp.text
        assert "P9" in resp.json()["detail"]

    @intent("INT-ESTIMATEKIT-017")
    def test_generate_refuses_a_phase_without_its_executive_summary_before_writing(
        self,
        client: TestClient,
        scaffolded_project: str,
        projects_root: Path,
    ) -> None:
        """INT-ESTIMATEKIT-017: no placeholder, and no other pipeline has run."""
        root = projects_root / scaffolded_project
        (root / "data/slides/P2-executive-summary.tsv").unlink()
        resp = client.post(f"/api/projects/{scaffolded_project}/generate", json={"phase": "P2"})
        assert resp.status_code == 422, resp.text
        assert "data/slides/P2-executive-summary.tsv" in resp.json()["detail"]
        assert not (root / "output" / "roadmap").exists()
        assert not (root / "output" / "excel").exists()

    @intent("INT-ESTIMATEKIT-017")
    def test_generate_renders_the_sold_phases_speaker_notes(
        self,
        client: TestClient,
        scaffolded_project: str,
        projects_root: Path,
    ) -> None:
        """INT-ESTIMATEKIT-017: the P2 deck speaks P2's notes, read from P2-notes.tsv."""
        root = projects_root / scaffolded_project
        p1_note = "The P1 estimate assumes a stable team."
        p2_note = "The P2 estimate assumes the P1 team continues."
        for phase_id, note in (("P1", p1_note), ("P2", p2_note)):
            (root / f"data/slides/{phase_id}-notes.tsv").write_text(
                f"Slide\tPosition\tText\neffort\tspeaker\t{note}\n", encoding="utf-8"
            )
        resp = client.post(f"/api/projects/{scaffolded_project}/generate", json={"phase": "P2"})
        assert resp.status_code == 200, resp.text
        page = root / "output/slides/pages/09-effort-estimate.md"
        content = page.read_text(encoding="utf-8")
        assert p2_note in content
        assert p1_note not in content

    def test_generate_creates_output_files(
        self,
        client: TestClient,
        scaffolded_project: str,
        projects_root: Path,
    ) -> None:
        client.post(
            f"/api/projects/{scaffolded_project}/generate",
            json={"pipelines": ["roadmap"]},
        )
        output_dir = projects_root / scaffolded_project / "output" / "roadmap"
        assert output_dir.exists()
        assert any(output_dir.iterdir()), "Roadmap output dir should contain files"

    def test_generate_missing_project_returns_404(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/projects/nonexistent/generate",
            json={"pipelines": ["roadmap"]},
        )
        assert resp.status_code == 404

    def test_generate_shows_up_in_outputs(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        """After generate, the outputs endpoint should list files."""
        client.post(
            f"/api/projects/{scaffolded_project}/generate",
            json={"pipelines": ["roadmap"]},
        )
        resp = client.get(f"/api/projects/{scaffolded_project}/outputs")
        assert resp.status_code == 200
        assert len(resp.json()["outputs"]) > 0


# ── Phases ───────────────────────────────────────────────────


class TestScaffoldPhase:
    """POST /api/projects/{slug}/phases/{phase_id}"""

    def test_minting_a_phase_writes_its_row_column_and_sentinel_marked_files(
        self,
        client: TestClient,
        scaffolded_project: str,
        projects_root: Path,
    ) -> None:
        resp = client.post(f"/api/projects/{scaffolded_project}/phases/P3")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["phase_id"] == "P3"
        files = set(body["files"])
        assert "data/requirements/02-phases.tsv" in files
        assert "data/requirements/03-matrix.tsv" in files
        for expected in (
            "data/activities/P3-build.tsv",
            "data/activities/P3-project.tsv",
            "data/activities/P3-resource.tsv",
            "data/activities/P3-config.tsv",
            "data/architecture/P3-components.tsv",
            "data/architecture/P3-overview.puml",
            "data/slides/P3-executive-summary.tsv",
            "data/slides/P3-notes.tsv",
        ):
            assert expected in files, expected

        root = projects_root / scaffolded_project
        phases = (root / "data/requirements/02-phases.tsv").read_text(encoding="utf-8")
        assert "\tP3\t" in phases
        matrix_header = (
            (root / "data/requirements/03-matrix.tsv")
            .read_text(encoding="utf-8").splitlines()[0].split("\t")
        )
        assert matrix_header[-2:] == ["Phase 3", "Notes"]
        pitch = (root / "data/slides/P3-executive-summary.tsv").read_text(encoding="utf-8")
        assert "[EXAMPLE]" in pitch
        assert "Phase 3" in pitch
        diagram = (root / "data/architecture/P3-overview.puml").read_text(encoding="utf-8")
        assert "Phase 3" in diagram

        summary = client.get(f"/api/projects/{scaffolded_project}/summary").json()
        assert summary["phases"] == ["P1", "P2", "P3"]

    def test_minting_an_existing_phase_is_refused(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(f"/api/projects/{scaffolded_project}/phases/P2")
        assert resp.status_code == 409, resp.text
        assert "P2" in resp.json()["detail"]

    def test_force_overwrites_the_phase_files(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(
            f"/api/projects/{scaffolded_project}/phases/P2", json={"force": True},
        )
        assert resp.status_code == 200, resp.text
        assert "data/activities/P2-build.tsv" in resp.json()["files"]

    def test_a_malformed_phase_id_is_refused(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        resp = client.post(f"/api/projects/{scaffolded_project}/phases/phase-three")
        assert resp.status_code == 400, resp.text

    def test_minting_on_a_missing_project_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/projects/nonexistent/phases/P3")
        assert resp.status_code == 404

    def test_a_minted_phase_audits_red_until_authored(
        self,
        client: TestClient,
        scaffolded_project: str,
    ) -> None:
        """The minted files are the phase's authoring to-do list, and nothing else breaks.

        Its sentinels fail the scaffold check, and its example build activities
        reference requirements the matrix does not yet assign to the new phase,
        which the reverse check names. Every structural check (headers, phase
        coverage, orphans, architecture, slides) passes on the minted set.
        """

        def sentinel_count(report: dict) -> int:
            message = next(
                c["message"] for c in report["checks"]
                if c["category"] == "scaffold" and c["outcome"] == "failed"
            )
            match = re.search(r"(\d+) scaffold sentinel", message)
            assert match, message
            return int(match.group(1))

        before = client.post(f"/api/projects/{scaffolded_project}/audit").json()
        client.post(f"/api/projects/{scaffolded_project}/phases/P3")
        resp = client.post(f"/api/projects/{scaffolded_project}/audit")
        assert resp.status_code == 200
        body = resp.json()
        failed = {
            (c["category"], c["name"]) for c in body["checks"] if c["outcome"] == "failed"
        }
        assert failed == {
            ("scaffold", "test_no_scaffold_sentinels_remain"),
            ("reverse", "test_reverse_coverage[P3]"),
        }, failed
        assert sentinel_count(body) > sentinel_count(before)


# ── Slug Validation ──────────────────────────────────────────


class TestSlugValidation:
    """Ensure slugs with traversal or special chars are rejected."""

    def test_traversal_slug_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/projects/../etc/summary")
        # FastAPI may normalise the path or the endpoint validates — either way not 200
        assert resp.status_code in (400, 404, 422)

    def test_slash_in_slug_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/projects/foo%2Fbar/summary")
        assert resp.status_code in (400, 404, 422)


# ── OpenAPI Schema ────────────────────────────────────────────


class TestOpenAPI:
    """Verify the auto-generated OpenAPI spec is served."""

    def test_openapi_json(self, client: TestClient) -> None:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "EstimateKit Engine"
        assert "/api/health" in schema["paths"]
