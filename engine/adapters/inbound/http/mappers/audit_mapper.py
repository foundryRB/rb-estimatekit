"""Mapper for auditor report responses."""

from __future__ import annotations

from engine.adapters.inbound.http.dtos.audit_report_response import (
    AuditCheckItem,
    AuditReportResponse,
    AuditSuggestionItem,
)
from engine.domain.model.value_objects.audit_report import AuditReport


def map_audit_report_response(report: AuditReport) -> AuditReportResponse:
    """Map domain AuditReport to HTTP response DTO."""
    return AuditReportResponse(
        checks=[
            AuditCheckItem(
                node_id=c.node_id,
                name=c.name,
                category=c.category,
                outcome=c.outcome,
                message=c.message,
            )
            for c in report.checks
        ],
        suggestions=[
            AuditSuggestionItem(
                code=s.code,
                title=s.title,
                detail=s.detail,
                category=s.category,
                severity=s.severity,
            )
            for s in report.suggestions
        ],
        passed_count=report.passed_count,
        failed_count=report.failed_count,
        skipped_count=report.skipped_count,
        passed=report.passed,
        duration_ms=report.duration_ms,
        phase=report.phase,
    )
