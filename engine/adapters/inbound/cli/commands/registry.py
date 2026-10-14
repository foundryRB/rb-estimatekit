"""CLI command registry — the declarative list of all CLI commands."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.inbound.cli.commands.arg import Arg
from engine.adapters.inbound.cli.commands.command_spec import CommandSpec
from engine.adapters.inbound.cli.mappers.audit_mapper import map_audit_report
from engine.adapters.inbound.cli.mappers.generation_mapper import map_generation_result
from engine.adapters.inbound.cli.mappers.summary_mapper import map_summary
from engine.adapters.inbound.cli.utils.formatters import (
    format_audit,
    format_discovered,
    format_pipeline_results,
    format_scaffolded,
    format_summary,
    format_written_files,
)
from engine.domain.model.value_objects.pipeline import Pipeline

__all__ = ["COMMANDS"]

COMMANDS: list[CommandSpec] = [
    CommandSpec(
        name="audit",
        help="Audit a project, or one phase plus shared integrity checks",
        container_method="run_audit",
        args=[
            Arg("project", help="Project directory", type=Path),
            Arg("--phase", help="Defined phase id; omit for the whole project"),
        ],
        execute_args={"project": "project_path", "phase": "phase"},
        mapper=map_audit_report,
        formatter=format_audit,
    ),
    CommandSpec(
        name="discover",
        help="Find projects under a root directory",
        container_method="discover_projects",
        args=[
            Arg("root", help="Projects root directory", type=Path),
        ],
        execute_args={"root": "projects_root"},
        formatter=format_discovered,
    ),
    CommandSpec(
        name="scaffold",
        help="Create a new project from templates",
        container_method="scaffold_project",
        args=[
            Arg("root", help="Projects root directory", type=Path),
            Arg("slug", help="Project slug (folder name)"),
            Arg("--force", help="Overwrite existing files", action="store_true"),
        ],
        execute_args={"root": "projects_root", "slug": "slug", "force": "force"},
        formatter=format_scaffolded,
    ),
    CommandSpec(
        name="scaffold-phase",
        help="Mint a phase (P<n>) in a project from the templates, sentinels included",
        container_method="scaffold_phase",
        args=[
            Arg("project", help="Project directory", type=Path),
            Arg("phase_id", help="Phase id, such as P3"),
            Arg("--force", help="Overwrite the phase's existing files", action="store_true"),
        ],
        execute_args={"project": "project_path", "phase_id": "phase_id", "force": "force"},
        formatter=format_written_files,
    ),
    CommandSpec(
        name="generate",
        help="Generate outputs (roadmap, excel, slides)",
        container_method="generate_all",
        args=[
            Arg("project", help="Project directory", type=Path),
            Arg(
                "--pipeline",
                help="Pipelines to run (default: all)",
                nargs="*",
                type=Pipeline,
                choices=[p.value for p in Pipeline],
            ),
            Arg(
                "--phase",
                help="Phase the slide deck sells (required when the project defines several)",
            ),
        ],
        execute_args={"project": "project_path", "pipeline": "pipelines", "phase": "phase"},
        mapper=map_generation_result,
        formatter=format_pipeline_results,
    ),
    CommandSpec(
        name="summary",
        help="Show a lightweight project summary",
        container_method="get_project_summary",
        args=[
            Arg("project", help="Project directory", type=Path),
        ],
        execute_args={"project": "project_path"},
        mapper=map_summary,
        formatter=format_summary,
    ),
]
