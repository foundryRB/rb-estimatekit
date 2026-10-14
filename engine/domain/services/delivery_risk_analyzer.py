"""Domain service: advisory delivery-risk suggestions for an estimate.

The auditor's checks are hard errors — a failing check means the plan's data
is incoherent and must be fixed for the plan to make sense. This service is
their advisory sibling: it raises *suggestions*, delivery risks learned from
experience with successful projects, without failing the audit. Tests give
errors that must be fixed; suggestions raise risks that violate experience and
stay advisory (estimatekit issue #1).

Pure domain logic: it is handed already-loaded phase inputs and returns
suggestions. All file I/O lives in the outbound adapter that feeds it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.constants.scheduling import is_qa_stream
from engine.domain.model.value_objects.audit_suggestion import AuditSuggestion
from engine.domain.model.value_objects.phase_config import PhaseConfig

__all__ = ["PhaseRiskInput", "ResourceAllocation", "analyze_delivery_risks"]

# ── Ratio bands ─────────────────────────────────────────────────────────────
# Learned from delivered projects; advisory, not hard gates. Tunable here.
DESIGN_BUILD_MIN_RATIO = 0.08  # design under ~8% of build under-derisks the build
QA_BUILD_MIN_RATIO = 0.15  # QA under ~15% of build correlates with defect leakage
OVERHEAD_BUILD_MAX_RATIO = 0.25  # management overhead over ~25% of build is top-heavy

# This many milestones in a single month reads as a delivery crunch.
MILESTONE_CLUSTER_THRESHOLD = 3

# Member-month allocations should land on this grid (5 / 10 / 15 / 20) so a
# person's plan is easy to manage; off-grid values like 3, 7, 21 are a smell.
ALLOCATION_STEP = 5
# This many up/down reversals in one member's allocation reads as an
# unrealistic zig-zag. A clean plan ramps up then down (at most one reversal).
OSCILLATION_MIN_REVERSALS = 2

# Substrings that classify a project.tsv stream name into an effort category.
# QA effort is the test streams' (is_qa_stream), the streams the audit's QA
# window check reads.
_DESIGN_KEYS = ("design",)
_BUILD_KEYS = ("dev", "build")
_OVERHEAD_KEYS = ("lead", "manage", "overhead", "governance")


@dataclass(frozen=True)
class ResourceAllocation:
    """One resource row's month-by-month allocation, in man-days.

    Attributes:
        label:    Profile / role that identifies the member, e.g. ``QA Engineer``.
        monthly:  Man-days per month in order, e.g. ``[10, 20, 20, 0]``.
    """

    label: str
    monthly: list[float]


@dataclass(frozen=True)
class PhaseRiskInput:
    """Everything the risk rules need about one phase, already loaded.

    Attributes:
        phase_id:       Phase identifier, e.g. ``P1``.
        config:         Scheduling parameters (design lead, testing lag, SIT/UAT).
        stream_effort:  ``project.tsv`` stream name → total effort in man-days,
                        e.g. ``{"1.Design": 30, "2.Dev": 100, "3.Test": 20}``.
        allocations:    Per-member monthly allocations from ``resource.tsv``.
    """

    phase_id: str
    config: PhaseConfig
    stream_effort: dict[str, float]
    allocations: list[ResourceAllocation] = field(default_factory=list)


def analyze_delivery_risks(
    phases: list[PhaseRiskInput],
    milestones_by_month: dict[str, int] | None = None,
) -> list[AuditSuggestion]:
    """Return advisory delivery-risk suggestions for the given phases.

    Findings are aggregated across phases: one suggestion per rule, naming the
    phases it applies to, so a systemic pattern reads as a single risk rather
    than N near-identical lines.
    """
    suggestions: list[AuditSuggestion] = []

    # ── Scheduling: zero design lead / zero testing lag ──
    ids = [p.phase_id for p in phases if p.config.design_lead_days <= 0]
    if ids:
        suggestions.append(
            AuditSuggestion(
                code="zero-design-lead",
                title="No design lead",
                detail=(
                    f"{_phrase(ids)} start build with a design lead of 0 days, so "
                    "build begins with no design runway. A zero design lead is a "
                    "red flag: it correlates with mid-build rework."
                ),
                category="scheduling",
            )
        )
    ids = [p.phase_id for p in phases if p.config.lag_pct <= 0]
    if ids:
        suggestions.append(
            AuditSuggestion(
                code="zero-testing-lag",
                title="No testing lag",
                detail=(
                    f"{_phrase(ids)} run QA fully concurrent with build (testing "
                    "lag 0%), leaving no stabilization tail. Zero lag correlates "
                    "with defects surfacing after handover."
                ),
                category="scheduling",
            )
        )

    # ── Coverage: missing SIT / UAT ──
    ids = [p.phase_id for p in phases if p.config.sit_days <= 0]
    if ids:
        suggestions.append(
            AuditSuggestion(
                code="no-sit",
                title="No SIT allocated",
                detail=(
                    f"{_phrase(ids)} allocate no System Integration Testing (SIT). "
                    "Integration defects surface late and cost the most to fix."
                ),
                category="coverage",
            )
        )
    ids = [p.phase_id for p in phases if p.config.uat_days <= 0]
    if ids:
        suggestions.append(
            AuditSuggestion(
                code="no-uat",
                title="No UAT allocated",
                detail=(
                    f"{_phrase(ids)} allocate no User Acceptance Testing (UAT). "
                    "Without UAT the customer signs off on unverified scope."
                ),
                category="coverage",
            )
        )

    # ── Ratios: design/build, QA/build, overhead/build ──
    thin_design: list[str] = []
    thin_qa: list[str] = []
    heavy_overhead: list[str] = []
    for p in phases:
        build = _category_effort(p.stream_effort, _BUILD_KEYS)
        if build <= 0:
            continue  # no build effort to compare against — nothing to say
        design = _category_effort(p.stream_effort, _DESIGN_KEYS)
        qa = sum(md for stream, md in p.stream_effort.items() if is_qa_stream(stream))
        overhead = _category_effort(p.stream_effort, _OVERHEAD_KEYS)
        if design / build < DESIGN_BUILD_MIN_RATIO:
            thin_design.append(f"{p.phase_id} ({_pct(design, build)})")
        if qa / build < QA_BUILD_MIN_RATIO:
            thin_qa.append(f"{p.phase_id} ({_pct(qa, build)})")
        if overhead > 0 and overhead / build > OVERHEAD_BUILD_MAX_RATIO:
            heavy_overhead.append(f"{p.phase_id} ({_pct(overhead, build)})")

    if thin_design:
        suggestions.append(
            AuditSuggestion(
                code="thin-design",
                title="Design light relative to build",
                detail=(
                    f"Design is under {_pct_of(DESIGN_BUILD_MIN_RATIO)} of build in "
                    f"{', '.join(thin_design)}. Thin design correlates with "
                    "build rework."
                ),
                category="ratios",
            )
        )
    if thin_qa:
        suggestions.append(
            AuditSuggestion(
                code="thin-qa",
                title="QA light relative to build",
                detail=(
                    f"QA is under {_pct_of(QA_BUILD_MIN_RATIO)} of build in "
                    f"{', '.join(thin_qa)}. Thin QA correlates with defect leakage."
                ),
                category="ratios",
            )
        )
    if heavy_overhead:
        suggestions.append(
            AuditSuggestion(
                code="heavy-overhead",
                title="Overhead heavy relative to build",
                detail=(
                    f"Overhead is over {_pct_of(OVERHEAD_BUILD_MAX_RATIO)} of build "
                    f"in {', '.join(heavy_overhead)}. A top-heavy plan spends much "
                    "of the budget off delivery."
                ),
                category="ratios",
            )
        )

    # ── Allocation shape: multiples of 5, and ramp not oscillate ──
    off_grid: list[str] = []
    zig_zag: list[str] = []
    for p in phases:
        for alloc in p.allocations:
            bad = [
                _fmt(v)
                for v in sorted({v for v in alloc.monthly if v > 0 and v % ALLOCATION_STEP})
            ]
            if bad:
                off_grid.append(f"{p.phase_id}/{alloc.label} ({', '.join(bad)})")
            if _reversals(alloc.monthly) >= OSCILLATION_MIN_REVERSALS:
                zig_zag.append(f"{p.phase_id}/{alloc.label}")

    if off_grid:
        suggestions.append(
            AuditSuggestion(
                code="off-grid-allocation",
                title="Allocations off the 5-day grid",
                detail=(
                    f"Member allocations should land on multiples of "
                    f"{ALLOCATION_STEP} (5, 10, 15, 20) to keep a person's plan "
                    f"manageable; these do not: {_join_capped(off_grid)}."
                ),
                category="allocation",
            )
        )
    if zig_zag:
        suggestions.append(
            AuditSuggestion(
                code="oscillating-allocation",
                title="Allocation swings up and down",
                detail=(
                    "A realistic allocation ramps up then down, not up and down "
                    f"repeatedly. These swing: {_join_capped(zig_zag)}."
                ),
                category="allocation",
            )
        )

    # ── Roadmap: milestones clustered into one month ──
    if milestones_by_month:
        crowded = sorted(
            (month, n)
            for month, n in milestones_by_month.items()
            if n >= MILESTONE_CLUSTER_THRESHOLD
        )
        if crowded:
            parts = ", ".join(f"{month} ({n})" for month, n in crowded)
            suggestions.append(
                AuditSuggestion(
                    code="milestone-cluster",
                    title="Milestones clustered in one month",
                    detail=(
                        f"Multiple milestones land in the same month: {parts}. "
                        "Milestones bunched together concentrate integration and "
                        "delivery risk; consider staggering them."
                    ),
                    category="scheduling",
                )
            )

    return suggestions


def _category_effort(stream_effort: dict[str, float], keys: tuple[str, ...]) -> float:
    """Sum effort across streams whose name contains any of *keys*."""
    return sum(
        md
        for stream, md in stream_effort.items()
        if any(k in stream.lower() for k in keys)
    )


def _phrase(ids: list[str]) -> str:
    """Render ids as 'Phase P1' / 'Phases P1 and P2' / 'Phases P1, P2 and P3'."""
    label = "Phase" if len(ids) == 1 else "Phases"
    if len(ids) == 1:
        return f"{label} {ids[0]}"
    if len(ids) == 2:
        return f"{label} {ids[0]} and {ids[1]}"
    return f"{label} {', '.join(ids[:-1])} and {ids[-1]}"


def _pct(part: float, whole: float) -> str:
    """Percentage of *part* over *whole*, rounded, e.g. ``21%``."""
    return f"{round(100 * part / whole)}%"


def _pct_of(ratio: float) -> str:
    """A ratio constant rendered as a percentage, e.g. ``8%``."""
    return f"{round(100 * ratio)}%"


def _reversals(monthly: list[float]) -> int:
    """Count up/down direction reversals after trimming leading/trailing zeros.

    A clean ramp (up then down) has one reversal; repeated swings have two or
    more. Leading and trailing zeros — before a member joins or after they
    leave — are ignored, and flat months do not count as a direction.
    """
    lo, hi = 0, len(monthly)
    while lo < hi and monthly[lo] == 0:
        lo += 1
    while hi > lo and monthly[hi - 1] == 0:
        hi -= 1
    seq = monthly[lo:hi]
    signs = [1 if b > a else -1 for a, b in zip(seq, seq[1:], strict=False) if b != a]
    return sum(1 for a, b in zip(signs, signs[1:], strict=False) if a != b)


def _fmt(value: float) -> str:
    """Render an allocation value without a trailing ``.0``."""
    return str(int(value)) if value == int(value) else str(value)


def _join_capped(items: list[str], cap: int = 8) -> str:
    """Join items, capping the tail with '… and N more' to keep detail readable."""
    if len(items) <= cap:
        return ", ".join(items)
    return ", ".join(items[:cap]) + f", and {len(items) - cap} more"
