"""Port: auditor runner — execute data-integrity checks against a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from engine.domain.model.value_objects.audit_report import AuditReport

__all__ = ["AuditorRunner"]


class AuditorRunner(Protocol):
    """Run the auditor suite against a project and return structured results."""

    def run(self, project_path: Path, phase: str | None = None) -> AuditReport:
        """Audit the whole project, or one phase plus shared integrity checks."""
        ...
