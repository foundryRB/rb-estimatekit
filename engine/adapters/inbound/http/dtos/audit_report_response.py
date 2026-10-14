"""Response DTO for auditor run results."""

from __future__ import annotations

from pydantic import BaseModel


class AuditCheckItem(BaseModel):
    """One data-integrity check outcome."""

    node_id: str
    name: str
    category: str
    outcome: str
    message: str


class AuditSuggestionItem(BaseModel):
    """One advisory delivery-risk suggestion (never affects ``passed``)."""

    code: str
    title: str
    detail: str
    category: str
    severity: str


class AuditReportResponse(BaseModel):
    """Response for ``POST /api/projects/{slug}/audit``."""

    checks: list[AuditCheckItem]
    suggestions: list[AuditSuggestionItem] = []
    passed_count: int
    failed_count: int
    skipped_count: int
    passed: bool
    duration_ms: int
    phase: str | None = None
