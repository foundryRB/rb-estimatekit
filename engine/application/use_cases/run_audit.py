"""Use case: Run auditor checks against a project."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from engine.application.events import AUDIT_COMPLETED, state_fact
from engine.application.ports.outbound.auditor_runner import AuditorRunner
from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.application.ports.outbound.suggestion_analyzer import SuggestionAnalyzer
from engine.domain.exceptions.project_not_found_error import ProjectNotFoundError
from engine.domain.model.value_objects.audit_report import AuditReport
from engine.logging import get_logger

logger = get_logger(__name__)


class RunAudit:
    """Execute the auditor suite for a project and return the report.

    The report carries both the hard check results (which decide ``passed``)
    and any advisory delivery-risk suggestions. Suggestions are computed after
    the checks and never affect ``passed``.
    """

    def __init__(
        self,
        runner: AuditorRunner,
        suggestions: SuggestionAnalyzer,
        events: EventPublisher | None = None,
    ) -> None:
        self._runner = runner
        self._suggestions = suggestions
        self._events = events

    def execute(self, project_path: Path, phase: str | None = None) -> AuditReport:
        """Validate the project exists, run checks, then attach suggestions."""
        if not (project_path / "project.yaml").exists():
            raise ProjectNotFoundError(project_path)
        report = (
            self._runner.run(project_path)
            if phase is None else self._runner.run(project_path, phase=phase)
        )
        report = replace(report, suggestions=self._safe_suggestions(project_path))
        log = logger.info if report.passed else logger.warning
        log(
            "Audit for %s: passed=%s (%d passed, %d failed, %d skipped, %d suggestions)",
            project_path.name,
            report.passed,
            report.passed_count,
            report.failed_count,
            report.skipped_count,
            len(report.suggestions),
        )
        # The report is in hand before the fact is stated: the verdict and the
        # counts ride along, the findings themselves stay in the report a caller
        # fetches (REF-Events section 5).
        state_fact(
            self._events,
            event_type=AUDIT_COMPLETED,
            subject=project_path.name,
            data={
                "project": project_path.name,
                "phase": report.phase,
                "verdict": "pass" if report.passed else "fail",
                "passed": report.passed_count,
                "failed": report.failed_count,
                "skipped": report.skipped_count,
                "suggestions": len(report.suggestions),
            },
        )
        return report

    def _safe_suggestions(self, project_path: Path) -> list:
        """Compute suggestions, swallowing errors — advisory never breaks the audit."""
        try:
            return self._suggestions.analyze(project_path)
        except Exception:  # noqa: BLE001 — advisory layer must not fail the audit
            logger.warning(
                "Suggestion analysis failed for %s; continuing without it",
                project_path.name,
                exc_info=True,
            )
            return []
