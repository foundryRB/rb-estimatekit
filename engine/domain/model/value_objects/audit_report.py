"""Domain value object: a single auditor check result."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.audit_suggestion import AuditSuggestion

__all__ = ["AuditCheckResult", "AuditReport"]


@dataclass(frozen=True)
class AuditCheckResult:
    """One data-integrity check outcome.

    Attributes:
        node_id:   Full pytest node identifier, e.g.
                   ``auditor/checks/tsv/test_validity.py::test_…[P1]``.
        name:      Short human label (the test function name + params).
        category:  Check category folder, e.g. ``tsv``, ``brd``, ``activity``.
        outcome:   ``passed``, ``failed``, or ``skipped``.
        message:   Failure/skip reason (empty string when passed).
    """

    node_id: str
    name: str
    category: str
    outcome: str  # "passed" | "failed" | "skipped"
    message: str


@dataclass(frozen=True)
class AuditReport:
    """Aggregated result of running the auditor against a project.

    Attributes:
        checks:         Individual check results.
        passed_count:   Number of checks that passed.
        failed_count:   Number of checks that failed.
        skipped_count:  Number of checks skipped.
        passed:         ``True`` when *every* non-skipped check passed.
        duration_ms:    Wall-clock time in milliseconds.
        phase:          Selected phase id, or None for the whole project.
        suggestions:    Advisory delivery-risk findings. These never affect
                        ``passed`` — they raise risks that violate experience
                        and stay advisory.
    """

    checks: list[AuditCheckResult]
    passed_count: int
    failed_count: int
    skipped_count: int
    passed: bool
    duration_ms: int
    suggestions: list[AuditSuggestion] = field(default_factory=list)
    phase: str | None = None
