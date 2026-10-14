"""MCP integration tests: a real server exercised through the protocol client.

TestClient cannot cover this surface: the MCP session manager only runs inside
the app lifespan, so these tests boot uvicorn on an ephemeral port and connect
with the official SDK client, exactly as a deployed agent would.
"""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from types import TracebackType

import httpx
import pytest
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import McpError
from pytest_intent import intent

import engine.adapters.inbound.http.dependencies as deps
from engine.adapters.inbound.http.app import create_app
from engine.adapters.outbound.plantuml.plantuml_renderer import PlantUmlRenderer


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _set_projects_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the server's projects root at a temp directory for every test."""
    monkeypatch.setenv("ESTIMATEKIT_PROJECTS_ROOT", str(tmp_path))
    deps.get_container.cache_clear()
    yield
    deps.get_container.cache_clear()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _Server:
    """Uvicorn on an ephemeral port, running the app for the test's duration."""

    def __init__(self) -> None:
        port = _free_port()
        config = uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_level="warning")
        self.base_url = f"http://127.0.0.1:{port}"
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def __enter__(self) -> _Server:
        self._thread.start()
        deadline = time.monotonic() + 15
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("test server failed to start")
            time.sleep(0.05)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)


async def _tool_names(base_url: str) -> set[str]:
    async with (
        streamable_http_client(f"{base_url}/mcp") as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        return {tool.name for tool in tools.tools}


async def _call(base_url: str, tool: str, args: dict) -> object:
    async with (
        streamable_http_client(f"{base_url}/mcp") as (read, write, _),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        return await session.call_tool(tool, args)


class TestMcpSurface:
    @pytest.mark.anyio
    async def test_audit_phase_selector_and_unknown_phase(self) -> None:
        """The public tool declares scope and refuses an undefined phase."""
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "phase-audit"})
            selected = await _call(
                srv.base_url, "run_audit", {"slug": "phase-audit", "phase": "P2"}
            )
            unknown = await _call(
                srv.base_url, "run_audit", {"slug": "phase-audit", "phase": "P99"}
            )
        assert not selected.isError
        assert selected.structuredContent["phase"] == "P2"
        assert "test_qa_timeline_feasibility[P1]" not in str(selected.content)
        assert unknown.isError and "Phase not found" in str(unknown.content)

    @intent("INT-MCP-002")
    @pytest.mark.anyio
    async def test_tool_list_mirrors_the_wired_inbound_ports(self) -> None:
        """INT-MCP-002: exactly the estimation-workflow operations, no more, no fewer."""
        with _Server() as srv:
            names = await _tool_names(srv.base_url)
        assert names == {
            "list_projects",
            "scaffold_project",
            "scaffold_phase",
            "delete_project",
            "rename_project",
            "archive_project",
            "unarchive_project",
            "get_project_summary",
            "list_project_files",
            "read_project_file",
            "list_architecture_diagrams",
            "render_architecture_diagram",
            "write_project_file",
            "append_project_rows",
            "replace_project_row",
            "delete_project_file",
            "run_audit",
            "generate_artifacts",
            "list_output_files",
            "get_guide",
        }

    @pytest.mark.anyio
    async def test_read_tool_returns_real_content(self) -> None:
        with _Server() as srv:
            result = await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            assert not result.isError
            summary = await _call(srv.base_url, "get_project_summary", {"slug": "mcp-proj"})
        assert not summary.isError
        assert "phase_count" in str(summary.content)

    @pytest.mark.anyio
    async def test_delete_tool_removes_the_project(self, tmp_path: Path) -> None:
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            assert (tmp_path / "mcp-proj").is_dir()
            deleted = await _call(srv.base_url, "delete_project", {"slug": "mcp-proj"})
            assert not deleted.isError
            listing = await _call(srv.base_url, "list_projects", {})
            missing = await _call(srv.base_url, "delete_project", {"slug": "mcp-proj"})
        assert not (tmp_path / "mcp-proj").exists()
        assert "mcp-proj" not in str(listing.content)
        # A second delete of the now-gone project surfaces the not-found reason.
        assert missing.isError

    @pytest.mark.anyio
    async def test_rename_tool_moves_the_slug_and_refuses_an_occupied_one(
        self, tmp_path: Path
    ) -> None:
        """The slug rename detaches the project from the old slug; an occupied
        target is refused with the reason."""
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            await _call(srv.base_url, "scaffold_project", {"slug": "occupied"})
            renamed = await _call(
                srv.base_url,
                "rename_project",
                {"slug": "mcp-proj", "new_slug": "mcp-proj-stale"},
            )
            assert not renamed.isError
            listing = await _call(srv.base_url, "list_projects", {})
            refused = await _call(
                srv.base_url,
                "rename_project",
                {"slug": "mcp-proj-stale", "new_slug": "occupied"},
            )
        assert not (tmp_path / "mcp-proj").exists()
        assert (tmp_path / "mcp-proj-stale" / "project.yaml").is_file()
        assert "mcp-proj-stale" in str(listing.content)
        assert refused.isError
        assert "exists" in str(refused.content)

    @pytest.mark.anyio
    async def test_diagram_tools_list_and_render(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The diagram reads answer over MCP: the scaffold's .puml sources are
        listed by name, and a render returns the SVG (renderer faked at the
        adapter seam so the test needs no JRE)."""
        monkeypatch.setattr(
            PlantUmlRenderer, "render_svg", lambda self, source: "<svg>fake</svg>"
        )
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            listing = await _call(
                srv.base_url, "list_architecture_diagrams", {"slug": "mcp-proj"}
            )
            rendered = await _call(
                srv.base_url,
                "render_architecture_diagram",
                {"slug": "mcp-proj", "name": "P1-overview"},
            )
        assert not listing.isError
        assert "P1-overview.puml" in str(listing.content)
        assert not rendered.isError
        assert "<svg>fake</svg>" in str(rendered.content)

    @pytest.mark.anyio
    async def test_archive_tools_park_and_revive_the_project(
        self, tmp_path: Path
    ) -> None:
        """Archived projects leave the active listing but keep their data."""
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            archived = await _call(srv.base_url, "archive_project", {"slug": "mcp-proj"})
            assert not archived.isError
            parked = await _call(srv.base_url, "list_projects", {})
            revived = await _call(srv.base_url, "unarchive_project", {"slug": "mcp-proj"})
            assert not revived.isError
            active = await _call(srv.base_url, "list_projects", {})
        assert (tmp_path / "mcp-proj" / "project.yaml").is_file()
        parked_body = str(parked.content)
        assert '"projects":[]' in parked_body.replace(" ", "")
        assert "mcp-proj" in parked_body
        active_body = str(active.content).replace(" ", "")
        assert '"archived":[]' in active_body
        assert "mcp-proj" in str(active.content)


class TestMcpSharedCore:
    @intent("INT-MCP-001")
    @pytest.mark.anyio
    async def test_write_over_mcp_is_visible_over_http(self, tmp_path: Path) -> None:
        """INT-MCP-001: MCP writes land in the same core the HTTP API reads."""
        content = "Slide\tPosition\tText\neffort\tspeaker\tvia MCP\n"
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            written = await _call(
                srv.base_url,
                "write_project_file",
                {"slug": "mcp-proj", "path": "data/slides/notes.tsv", "content": content},
            )
            assert not written.isError
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{srv.base_url}/api/projects/mcp-proj/files/data/slides/notes.tsv"
                )
        assert res.status_code == 200
        assert res.json()["content"] == content
        assert (tmp_path / "mcp-proj" / "data" / "slides" / "notes.tsv").is_file()

    @intent("INT-MCP-001")
    @pytest.mark.anyio
    async def test_path_containment_holds_on_the_mcp_door(self) -> None:
        """INT-MCP-001: the same containment rules reject an escaping path, with the reason."""
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            escape = await _call(
                srv.base_url,
                "write_project_file",
                {"slug": "mcp-proj", "path": "../evil.txt", "content": "nope"},
            )
            bad_slug = await _call(srv.base_url, "get_project_summary", {"slug": "../etc"})
        assert escape.isError
        assert "escapes" in str(escape.content)
        assert bad_slug.isError
        assert "slug" in str(bad_slug.content).lower()

    @intent("INT-MCP-001")
    @pytest.mark.anyio
    async def test_delete_over_mcp_removes_the_file(self, tmp_path: Path) -> None:
        """INT-MCP-001: an MCP delete removes the file from the same core the HTTP API reads."""
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            await _call(
                srv.base_url,
                "write_project_file",
                {"slug": "mcp-proj", "path": "data/slides/scratch.tsv", "content": "A\tB\n"},
            )
            deleted = await _call(
                srv.base_url,
                "delete_project_file",
                {"slug": "mcp-proj", "path": "data/slides/scratch.tsv"},
            )
            assert not deleted.isError
            # A second delete of the now-gone file surfaces the not-found reason.
            missing = await _call(
                srv.base_url,
                "delete_project_file",
                {"slug": "mcp-proj", "path": "data/slides/scratch.tsv"},
            )
        assert missing.isError
        assert not (tmp_path / "mcp-proj" / "data" / "slides" / "scratch.tsv").exists()

    @intent("INT-MCP-001")
    @pytest.mark.anyio
    async def test_row_writes_over_mcp_are_visible_over_http(self, tmp_path: Path) -> None:
        """INT-MCP-001: rows appended and replaced over MCP land in the core HTTP reads."""
        rel = "data/requirements/01-brd.tsv"
        row = {
            "Category": "Auth",
            "Req ID": "AUTH-002",
            "Description": "Single sign-on",
            "Original Text": "Users sign in once",
            "Lines": "2",
        }
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            appended = await _call(
                srv.base_url,
                "append_project_rows",
                {"slug": "mcp-proj", "path": rel, "rows": [row]},
            )
            replaced = await _call(
                srv.base_url,
                "replace_project_row",
                {
                    "slug": "mcp-proj",
                    "path": rel,
                    "row_id": "AUTH-002",
                    "row": {**row, "Description": "SSO for every app"},
                },
            )
            refused = await _call(
                srv.base_url,
                "append_project_rows",
                {"slug": "mcp-proj", "path": rel, "rows": [{"Req ID": "AUTH-003"}]},
            )
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{srv.base_url}/api/projects/mcp-proj/files/{rel}")
        assert not appended.isError and not replaced.isError
        lines = res.json()["content"].splitlines()
        assert lines[-1] == "Auth\tAUTH-002\tSSO for every app\tUsers sign in once\t2"
        assert refused.isError
        assert "missing column" in str(refused.content)


class TestMcpPrompts:
    @pytest.mark.anyio
    async def test_estimate_project_prompt_carries_the_runbook(self) -> None:
        """The prompt is the invocable form of the estimation loop."""
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                prompts = await session.list_prompts()
                names = {prompt.name for prompt in prompts.prompts}
                result = await session.get_prompt("estimate-project", {"slug": "fresh-proj"})
        assert "estimate-project" in names
        text = str(result.messages[0].content)
        assert "scaffold_project" in text
        assert "run_audit" in text
        assert "fresh-proj" in text

    @pytest.mark.anyio
    async def test_estimate_project_prompt_reads_the_live_state(self) -> None:
        """An existing project gets a continue-the-loop runbook, not a scaffold one."""
        with _Server() as srv:
            await _call(srv.base_url, "scaffold_project", {"slug": "mcp-proj"})
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.get_prompt("estimate-project", {"slug": "mcp-proj"})
        text = str(result.messages[0].content)
        assert "exists" in text
        assert "Skip scaffolding" in text

    @pytest.mark.anyio
    async def test_estimate_project_prompt_rejects_an_invalid_slug(self) -> None:
        with _Server() as srv:
            async with (
                streamable_http_client(f"{srv.base_url}/mcp") as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                with pytest.raises(McpError):
                    await session.get_prompt("estimate-project", {"slug": "../evil"})


class TestMcpDeploymentSurface:
    @pytest.mark.anyio
    async def test_bare_mcp_path_works_with_the_spa_mounted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clients connect to /mcp (no slash); the SPA mount at / must not swallow it."""
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "index.html").write_text("<html>spa</html>", encoding="utf-8")
        monkeypatch.setenv("ESTIMATEKIT_FRONTEND_DIST", str(dist))
        with _Server() as srv:
            names = await _tool_names(srv.base_url)
        assert "run_audit" in names

    @pytest.mark.anyio
    async def test_allowed_hosts_gate_the_transport(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A deployment allows its public hostname; other Host values answer 421."""
        initialize = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "probe", "version": "0"},
            },
        }
        headers = {"Accept": "application/json, text/event-stream"}
        monkeypatch.setenv("ESTIMATEKIT_MCP_ALLOWED_HOSTS", "estimatekit.example.test")
        with _Server() as srv:
            async with httpx.AsyncClient() as client:
                wrong_host = await client.post(
                    f"{srv.base_url}/mcp/", json=initialize, headers=headers
                )
                right_host = await client.post(
                    f"{srv.base_url}/mcp/",
                    json=initialize,
                    headers={**headers, "Host": "estimatekit.example.test"},
                )
        assert wrong_host.status_code == 421
        assert right_host.status_code == 200
