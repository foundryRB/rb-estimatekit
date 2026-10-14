"""CLI output formatters — present use-case results to the terminal."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from engine.logging import get_logger

if TYPE_CHECKING:
    from engine.adapters.inbound.cli.dtos.audit_report_view import AuditReportView
    from engine.adapters.inbound.cli.dtos.generation_result_view import GenerationResultView
    from engine.adapters.inbound.cli.dtos.summary_view import SummaryView
    from engine.domain.model.value_objects.discovered_project import DiscoveredProject

logger = get_logger(__name__)

__all__ = [
    "format_discovered",
    "format_audit",
    "format_pipeline_results",
    "format_scaffolded",
    "format_summary",
    "format_written_files",
]


def format_discovered(result: list[DiscoveredProject]) -> int:
    """Print each discovered project path, flagging archived ones."""
    for entry in result:
        suffix = "  (archived)" if entry.archived else ""
        sys.stdout.write(f"{entry.path}{suffix}\n")
    return 0


def format_scaffolded(result: Path) -> int:
    """Log the scaffolded path."""
    logger.info("Scaffolded: %s", result)
    return 0


def format_written_files(result: list[str]) -> int:
    """Print each project-relative path the command wrote."""
    for path in result:
        sys.stdout.write(f"{path}\n")
    return 0


def format_pipeline_results(result: GenerationResultView) -> int:
    """Log each pipeline result, return non-zero on any failure."""
    for outcome in result.outcomes:
        level = "info" if outcome.success else "error"
        detail = f" ({result.phase})" if outcome.name == "slides" and result.phase else ""
        getattr(logger, level)(
            "  %s: %s%s", outcome.name, "OK" if outcome.success else "FAIL", detail,
        )
    return 0 if result.success else 1


def format_summary(result: SummaryView) -> int:
    """Print the project summary."""
    phases = f" ({', '.join(result.phases)})" if result.phases else ""
    sys.stdout.write(
        f"Project:      {result.name}\n"
        f"Client:       {result.client}\n"
        f"Phases:       {result.phase_count}{phases}\n"
        f"Requirements: {result.requirement_count}\n"
        f"Assumptions:  {result.assumption_count}\n"
    )
    return 0


def format_audit(report: AuditReportView) -> int:
    """Print the scoped audit report and return its verdict as an exit code."""
    print(json.dumps(asdict(report)))
    return 0 if report.passed else 1
