"""Domain value object: one advisory delivery-risk suggestion."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AuditSuggestion"]


@dataclass(frozen=True)
class AuditSuggestion:
    """One advisory delivery-risk finding.

    Suggestions are *advisory*, the counterpart to an ``AuditCheckResult``
    failure. A failing check means the data is incoherent and must be fixed;
    a suggestion flags a plan shape that violates delivery experience — a red
    flag worth a second look — without failing the audit or blocking
    generation. The estimator keeps the call.

    Attributes:
        code:      Stable identifier for the rule, e.g. ``zero-design-lead``.
        title:     Short human label.
        detail:    The specific finding, naming the phases / numbers involved.
        category:  Grouping — ``scheduling``, ``coverage``, or ``ratios``.
        severity:  Advisory level; ``warning`` today (room for ``info``).
    """

    code: str
    title: str
    detail: str
    category: str
    severity: str = "warning"
