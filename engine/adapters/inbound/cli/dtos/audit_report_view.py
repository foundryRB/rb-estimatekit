"""CLI-layer representation of a scoped audit report."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AuditReportView"]


@dataclass(frozen=True)
class AuditReportView:
    """Public audit fields presented by the CLI."""

    checks: list[dict[str, str]]
    passed_count: int
    failed_count: int
    skipped_count: int
    passed: bool
    duration_ms: int
    suggestions: list[dict[str, str]]
    phase: str | None
