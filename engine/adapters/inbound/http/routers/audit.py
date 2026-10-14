"""Routes: auditor — run data-integrity checks against a project."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine.adapters.inbound.http.dependencies import get_container
from engine.adapters.inbound.http.dtos.audit_report_response import AuditReportResponse
from engine.adapters.inbound.http.mappers.audit_mapper import map_audit_report_response
from engine.container import Container

router = APIRouter()


@router.post("/{slug}/audit", response_model=AuditReportResponse)
async def run_audit(
    slug: str,
    phase: str | None = None,
    container: Container = Depends(get_container),  # noqa: B008
) -> AuditReportResponse:
    """Audit one phase plus shared integrity, or the whole project when phase is omitted."""
    project_path = container.project_path(slug)
    report = container.run_audit().execute(project_path, phase=phase)
    return map_audit_report_response(report)
