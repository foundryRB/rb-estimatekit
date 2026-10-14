"""Inbound port: run auditor data-integrity checks against a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from engine.domain.model.value_objects.audit_report import AuditReport

__all__ = ["RunAuditPort"]


@runtime_checkable
class RunAuditPort(Protocol):
    """Audit the whole project, or one phase plus shared integrity checks."""

    def execute(self, project_path: Path, phase: str | None = None) -> AuditReport:
        """Run the auditor against *project_path*."""
        ...
