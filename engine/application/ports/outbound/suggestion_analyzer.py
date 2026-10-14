"""Port: suggestion analyzer — advisory delivery-risk findings for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from engine.domain.model.value_objects.audit_suggestion import AuditSuggestion

__all__ = ["SuggestionAnalyzer"]


class SuggestionAnalyzer(Protocol):
    """Analyze a project's inputs for advisory delivery risks.

    Suggestions never fail the audit; an analyzer that cannot compute them
    should return an empty list rather than raise.
    """

    def analyze(self, project_path: Path) -> list[AuditSuggestion]:
        """Return advisory delivery-risk suggestions for the project."""
        ...
