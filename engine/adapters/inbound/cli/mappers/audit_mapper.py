"""Mapper: domain audit report to its CLI representation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.adapters.inbound.cli.dtos.audit_report_view import AuditReportView

if TYPE_CHECKING:
    from engine.domain.model.value_objects.audit_report import AuditReport

__all__ = ["map_audit_report"]


def map_audit_report(report: AuditReport) -> AuditReportView:
    """Copy the public audit fields into the adapter's presentation type."""
    return AuditReportView(
        checks=[
            {
                "node_id": check.node_id,
                "name": check.name,
                "category": check.category,
                "outcome": check.outcome,
                "message": check.message,
            }
            for check in report.checks
        ],
        passed_count=report.passed_count,
        failed_count=report.failed_count,
        skipped_count=report.skipped_count,
        passed=report.passed,
        duration_ms=report.duration_ms,
        suggestions=[
            {
                "code": suggestion.code,
                "title": suggestion.title,
                "detail": suggestion.detail,
                "category": suggestion.category,
                "severity": suggestion.severity,
            }
            for suggestion in report.suggestions
        ],
        phase=report.phase,
    )
