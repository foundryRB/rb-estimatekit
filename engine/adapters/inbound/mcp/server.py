"""MCP inbound adapter: tools mirroring the inbound ports (streamable HTTP).

A third door into the same use cases as the SPA, REST API, and CLI: every call
goes through the container's inbound ports, so slug validation, path
containment, and the audit gate behave identically on every surface.

Serialization reuses the HTTP DTO mappers: the OpenAPI contract is the engine's
single serialization surface, and the MCP tools mirror it mechanically rather
than maintaining a parallel shape. Binary transfer (output download, ZIP
export/import) stays on the HTTP API; the tools report where the artifacts
live instead of streaming them.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings

from engine.adapters.inbound.http.mappers.archive_mapper import map_archive_response
from engine.adapters.inbound.http.mappers.audit_mapper import map_audit_report_response
from engine.adapters.inbound.http.mappers.delete_mapper import map_delete_response
from engine.adapters.inbound.http.mappers.diagrams_mapper import (
    map_diagram_svg_response,
    map_list_diagrams_response,
)
from engine.adapters.inbound.http.mappers.discover_mapper import map_discover_response
from engine.adapters.inbound.http.mappers.files_mapper import (
    map_file_content_response,
    map_list_files_response,
    map_list_outputs_response,
)
from engine.adapters.inbound.http.mappers.generate_mapper import map_generate_response
from engine.adapters.inbound.http.mappers.phase_mapper import map_scaffold_phase_response
from engine.adapters.inbound.http.mappers.project_summary_mapper import (
    map_project_summary_response,
)
from engine.adapters.inbound.http.mappers.rename_mapper import map_rename_response
from engine.adapters.inbound.http.mappers.scaffold_mapper import map_scaffold_response
from engine.container import Container
from engine.domain.exceptions import AppError
from engine.domain.model.value_objects.pipeline import Pipeline

__all__ = ["build_mcp_server"]

_INSTRUCTIONS = (
    "Project-estimation engine: structured project data (YAML + TSV) in, audited "
    "and scheduled delivery artifacts (roadmap, Excel workbooks, slide deck) out. "
    "The estimation loop: scaffold_project, rewrite the data files from the "
    "engagement brief (keep every TSV header row byte-identical), run_audit until "
    "it passes, then generate_artifacts. Read get_guide before authoring: it is "
    "the authoring reference for the file layout and which files repeat per "
    "phase, the header-row contract, how a phase is minted, what each audit "
    "category verifies, what each pipeline produces, and which transfers are "
    "HTTP-only. A failing audit means the numbers cannot "
    "be trusted; the audit refuses scaffold sentinels ([EXAMPLE], [PROJECT NAME]) "
    "in any data file, so a fresh scaffold audits red until every example value — "
    "including the per-phase architecture diagrams — is authored or deleted. "
    "The slide deck sells one phase: on a project with several phases, pass the "
    "phase to generate_artifacts, and mint a new phase with scaffold_phase so its "
    "files (activities, architecture, executive summary, notes) arrive "
    "sentinel-marked. "
    "Generated artifacts stay on the instance: download workbooks over "
    "the HTTP API (/api/projects/<slug>/outputs/<path>) and review the deck at "
    "/projects/<slug>/slides/."
)

_ALLOWED_HOSTS_ENV = "ESTIMATEKIT_MCP_ALLOWED_HOSTS"


def _transport_security() -> TransportSecuritySettings | None:
    """DNS-rebinding protection for the transport.

    The SDK default admits localhost only, which is right for the local run.
    A deployment serves on a public hostname, so the chart supplies it via
    $ESTIMATEKIT_MCP_ALLOWED_HOSTS (comma-separated Host header values).
    """
    raw = os.environ.get(_ALLOWED_HOSTS_ENV)
    if not raw:
        return None
    hosts = [h.strip() for h in raw.split(",") if h.strip()]
    return TransportSecuritySettings(allowed_hosts=hosts)


def build_mcp_server(container: Container) -> FastMCP:
    """Build the MCP server over the container's wired use cases."""
    server = FastMCP(
        "estimatekit",
        instructions=_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
        transport_security=_transport_security(),
    )

    @server.tool()
    def list_projects() -> dict[str, Any]:
        """Return the active project slugs, with archived (parked) slugs listed separately."""
        entries = _guard(lambda: container.discover_projects().execute(container.projects_root))
        return map_discover_response(entries).model_dump()

    @server.tool()
    def scaffold_project(slug: str, force: bool = False) -> dict[str, Any]:
        """Create a project from the built-in templates.

        The example is internally consistent; its only audit failures are its
        [EXAMPLE]/[PROJECT NAME] sentinels, which list what remains to author.
        """
        def _do() -> Any:
            container.project_path(slug)  # validates the slug
            return container.scaffold_project().execute(
                projects_root=container.projects_root, slug=slug, force=force
            )
        return map_scaffold_response(_guard(_do)).model_dump()

    @server.tool()
    def scaffold_phase(slug: str, phase_id: str, force: bool = False) -> dict[str, Any]:
        """Mint a phase (P<n>) in an existing project from the templates.

        Adds the phase's row to 02-phases.tsv and its column to 03-matrix.tsv,
        and copies its whole file set (activities, components, diagram,
        executive summary, notes) with every example value sentinel-marked, so
        the audit refuses the phase until each file is authored or deleted.
        """
        def _do() -> Any:
            return container.scaffold_phase().execute(
                container.project_path(slug), phase_id, force=force
            )
        return map_scaffold_phase_response(slug, phase_id, _guard(_do)).model_dump()

    @server.tool()
    def delete_project(slug: str) -> dict[str, Any]:
        """Permanently delete a project and all its data. Irreversible; there is no undo."""
        def _do() -> Any:
            container.project_path(slug)  # validates the slug
            return container.delete_project().execute(
                projects_root=container.projects_root, slug=slug
            )
        return map_delete_response(_guard(_do)).model_dump()

    @server.tool()
    def rename_project(
        slug: str, new_slug: str | None = None, new_name: str | None = None
    ) -> dict[str, Any]:
        """Rename a project's display name (new_name) and/or its slug (new_slug).

        Renaming a slug detaches the project from whatever joins on the old
        slug - use it when a stale estimation must stop answering for a live
        repo. The folder moves atomically; an occupied or malformed target
        slug is refused with the reason.
        """
        def _do() -> Any:
            container.project_path(slug)  # validates the slug
            if new_slug is not None:
                container.project_path(new_slug)  # validates the target slug
            return container.rename_project().execute(
                projects_root=container.projects_root,
                slug=slug,
                new_slug=new_slug,
                new_name=new_name,
            )
        return map_rename_response(slug, _guard(_do)).model_dump()

    @server.tool()
    def archive_project(slug: str) -> dict[str, Any]:
        """Park a project: all data stays, but it drops out of the active listing."""
        def _do() -> Any:
            container.project_path(slug)  # validates the slug
            return container.archive_project().execute(
                projects_root=container.projects_root, slug=slug
            )
        return map_archive_response(_guard(_do), archived=True).model_dump()

    @server.tool()
    def unarchive_project(slug: str) -> dict[str, Any]:
        """Return an archived project to the active listing, data untouched."""
        def _do() -> Any:
            container.project_path(slug)  # validates the slug
            return container.unarchive_project().execute(
                projects_root=container.projects_root, slug=slug
            )
        return map_archive_response(_guard(_do), archived=False).model_dump()

    @server.tool()
    def get_project_summary(slug: str) -> dict[str, Any]:
        """Return a project's name, client, and phase/requirement/assumption counts."""
        summary = _guard(
            lambda: container.get_project_summary().execute(container.project_path(slug))
        )
        return map_project_summary_response(summary).model_dump()

    @server.tool()
    def list_project_files(slug: str) -> dict[str, Any]:
        """List every editable data file in a project, with kind and directory."""
        files = _guard(
            lambda: container.list_project_files().execute(container.project_path(slug))
        )
        return map_list_files_response(files).model_dump()

    @server.tool()
    def read_project_file(slug: str, path: str) -> dict[str, Any]:
        """Read the raw text of one project file (project-relative path)."""
        content = _guard(
            lambda: container.read_project_file().execute(container.project_path(slug), path)
        )
        return map_file_content_response(path, content).model_dump()

    @server.tool()
    def list_architecture_diagrams(slug: str) -> dict[str, Any]:
        """List the project's architecture diagram sources (.puml) by name and path."""
        diagrams = _guard(
            lambda: container.list_architecture_diagrams().execute(container.project_path(slug))
        )
        return map_list_diagrams_response(diagrams).model_dump()

    @server.tool()
    def render_architecture_diagram(slug: str, name: str) -> dict[str, Any]:
        """Render one architecture diagram to SVG in-process; nothing leaves the pod."""
        svg = _guard(
            lambda: container.render_architecture_diagram().execute(
                container.project_path(slug), name
            )
        )
        return map_diagram_svg_response(name, svg).model_dump()

    @server.tool()
    def write_project_file(slug: str, path: str, content: str) -> dict[str, Any]:
        """Create or overwrite one project data file. Keep TSV header rows byte-identical."""
        _guard(
            lambda: container.write_project_file().execute(
                container.project_path(slug), path, content
            )
        )
        return {"saved": True, "path": path}

    @server.tool()
    def append_project_rows(slug: str, path: str, rows: list[dict[str, str]]) -> dict[str, Any]:
        """Append rows to one TSV data file without re-sending the rows it holds.

        Each row maps every column of the file's header row, by its exact name,
        to the cell's text; in a file with an ID column (Req ID, Activity ID, ...)
        each row carries a non-blank ID new to the file. A row that misses or adds
        a column, a cell holding a tab or a line break or starting with a double
        quote, or a repeated ID is refused with the reason and nothing is written.
        A file the engine reads differently from its lines and tabs (mixed line
        endings, a quoted cell spanning lines, a repeated header name) is refused
        as a whole; rewrite it with write_project_file.
        """
        count = _guard(
            lambda: container.append_project_rows().execute(
                container.project_path(slug), path, rows
            )
        )
        return {"appended": count, "path": path}

    @server.tool()
    def replace_project_row(
        slug: str, path: str, row_id: str, row: dict[str, str]
    ) -> dict[str, Any]:
        """Replace the one row of a TSV data file whose ID column holds row_id.

        The ID column is the header's first column named '... ID' (Req ID,
        Activity ID, Assumption ID, Guideline ID, Phase ID). The row maps every
        header column to its cell and keeps its ID; every other row is left as
        it was. No match, several matches, a row that does not fit the header, or
        a cell starting with a double quote is refused with the reason and nothing
        is written. A file the engine reads differently from its lines and tabs
        (mixed line endings, a quoted cell spanning lines, a repeated header name)
        is refused as a whole; rewrite it with write_project_file.
        """
        _guard(
            lambda: container.replace_project_row().execute(
                container.project_path(slug), path, row_id, row
            )
        )
        return {"replaced": row_id, "path": path}

    @server.tool()
    def delete_project_file(slug: str, path: str) -> dict[str, Any]:
        """Delete one project data file (drop scaffolded files a project no longer needs)."""
        _guard(
            lambda: container.delete_project_file().execute(
                container.project_path(slug), path
            )
        )
        return {"deleted": True, "path": path}

    @server.tool()
    def run_audit(slug: str, phase: str | None = None) -> dict[str, Any]:
        """Audit one phase plus shared integrity, or the whole project when phase is omitted."""
        report = _guard(
            lambda: container.run_audit().execute(container.project_path(slug), phase=phase)
        )
        return map_audit_report_response(report).model_dump()

    @server.tool()
    def generate_artifacts(
        slug: str, pipelines: list[str] | None = None, phase: str | None = None
    ) -> dict[str, Any]:
        """Run generation pipelines (roadmap, excel, slides); omit pipelines to run all.

        The slide deck sells one phase: pass its id as phase. A single-phase
        project needs none; a multi-phase project refuses slides without it.
        """
        try:
            selected = [Pipeline(p) for p in pipelines] if pipelines else None
        except ValueError as exc:
            valid = ", ".join(p.value for p in Pipeline)
            raise ToolError(f"unknown pipeline; valid values: {valid}") from exc
        result = _guard(
            lambda: container.generate_all().execute(
                container.project_path(slug),
                pipelines=selected,
                phase=phase,
                slides_base_path=f"/projects/{slug}/slides/",
            )
        )
        return map_generate_response(result).model_dump()

    @server.tool()
    def list_output_files(slug: str) -> dict[str, Any]:
        """List the generated artifacts (download them over the HTTP API)."""
        outputs = _guard(
            lambda: container.list_output_files().execute(container.project_path(slug))
        )
        return map_list_outputs_response(outputs).model_dump()

    @server.tool()
    def get_guide() -> dict[str, Any]:
        """Return the authoring guide: the stages from a scaffold to delivered artifacts.

        It holds the project layout and which files repeat per phase, the
        header-row contract, how a phase is minted, what each audit category
        verifies, what each pipeline produces, and which transfers are HTTP-only.
        """
        return _guard(container.read_guide)

    @server.prompt(
        name="estimate-project",
        title="Estimate a project",
        description=(
            "Run the full estimation loop on a project: scaffold, author the data "
            "from the engagement brief, audit until clean, generate the artifacts."
        ),
    )
    def estimate_project(slug: str) -> str:
        """The estimation runbook, parametrized with the project's live state."""
        container.project_path(slug)  # validates the slug before writing a runbook for it
        existing = {
            e.path.name for e in container.discover_projects().execute(container.projects_root)
        }
        if slug in existing:
            summary = container.get_project_summary().execute(container.project_path(slug))
            opening = (
                f"Project '{slug}' exists: {summary.name} for {summary.client}, "
                f"{summary.phase_count} phase(s), {summary.requirement_count} requirement(s). "
                "Skip scaffolding and continue its estimation loop.\n\n"
            )
        else:
            opening = (
                f"Project '{slug}' does not exist yet. Call scaffold_project with "
                f"slug='{slug}' first; the result is a complete example data set that "
                "shows each file's expected shape. Every example value carries a "
                "sentinel ([EXAMPLE], [PROJECT NAME]) and the audit fails while any "
                "sentinel remains, so the audit report doubles as the authoring "
                "to-do list.\n\n"
            )
        return (
            f"Estimate project '{slug}' on this estimatekit instance.\n\n"
            + opening
            + "1. Collect the engagement brief (requirements, phasing, team shape, "
            "assumptions) from the user if you do not have it.\n"
            "2. Call list_project_files, then read each file you will change with "
            "read_project_file BEFORE writing it: the TSV header row is the parsing "
            "contract and must stay byte-identical.\n"
            "3. Author requirements first (01-brd.tsv, 02-phases.tsv, 03-matrix.tsv), "
            "then per-phase build activities referencing Req IDs with effort in MD, "
            "the resource plan, the assumptions, and the phase's own pitch "
            "(P<n>-executive-summary.tsv, P<n>-notes.tsv), using write_project_file. "
            "Mint any further phase with scaffold_phase, so its files arrive "
            "sentinel-marked.\n"
            "4. Call run_audit after every editing pass and fix failures before "
            "continuing. Loop until the report says passed=true; never deliver over "
            "a failing audit.\n"
            "5. Call generate_artifacts (all pipelines) naming the phase the deck "
            "sells, then list_output_files.\n"
            "6. Hand the user the deck at <instance base URL>/projects/" + slug
            + "/slides/ and the workbook download paths under "
            "/api/projects/" + slug + "/outputs/."
        )

    return server


def _guard(fn: Any) -> Any:
    """Run a port call, surfacing domain failures as tool errors with their reason."""
    try:
        return fn()
    except AppError as exc:
        raise ToolError(str(exc)) from exc
