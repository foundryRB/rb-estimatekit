"""DeliveryRiskAnalyzer — advisory delivery-risk suggestions over phase inputs.

Attests INT-ESTIMATEKIT-011: an audit surfaces advisory delivery-risk
suggestions (zero design lead / testing lag, missing SIT/UAT, off-band
effort ratios, clustered milestones) that stay advisory.
"""

from __future__ import annotations

from pytest_intent import intent

from engine.domain.model.value_objects.phase_config import PhaseConfig
from engine.domain.services.delivery_risk_analyzer import (
    PhaseRiskInput,
    ResourceAllocation,
    analyze_delivery_risks,
)


def _phase(
    phase_id: str = "P1",
    *,
    design_lead_days: float = 5.0,
    lag_pct: float = 10.0,
    sit_days: float = 5.0,
    uat_days: float = 5.0,
    design: float = 20.0,
    build: float = 100.0,
    qa: float = 20.0,
    qa_stream: str = "3.Test",
    overhead: float = 0.0,
    allocations: list[ResourceAllocation] | None = None,
) -> PhaseRiskInput:
    """A phase whose defaults trip no rule; override one field to trip a rule."""
    stream_effort: dict[str, float] = {
        "1.Design": design,
        "2.Dev": build,
        qa_stream: qa,
    }
    if overhead:
        stream_effort["0.Lead"] = overhead
    return PhaseRiskInput(
        phase_id=phase_id,
        config=PhaseConfig(
            design_lead_days=design_lead_days,
            lag_pct=lag_pct,
            sit_days=sit_days,
            uat_days=uat_days,
        ),
        stream_effort=stream_effort,
        allocations=allocations or [],
    )


def _codes(phases: list[PhaseRiskInput]) -> set[str]:
    return {s.code for s in analyze_delivery_risks(phases)}


def test_healthy_phase_raises_no_suggestions() -> None:
    assert analyze_delivery_risks([_phase()]) == []


def test_zero_design_lead_flagged() -> None:
    assert "zero-design-lead" in _codes([_phase(design_lead_days=0)])


def test_zero_testing_lag_flagged() -> None:
    assert "zero-testing-lag" in _codes([_phase(lag_pct=0)])


def test_positive_lead_and_lag_not_flagged() -> None:
    codes = _codes([_phase(design_lead_days=3, lag_pct=15)])
    assert "zero-design-lead" not in codes
    assert "zero-testing-lag" not in codes


def test_missing_sit_flagged() -> None:
    assert "no-sit" in _codes([_phase(sit_days=0)])


def test_missing_uat_flagged() -> None:
    assert "no-uat" in _codes([_phase(uat_days=0)])


def test_present_sit_uat_not_flagged() -> None:
    codes = _codes([_phase(sit_days=10, uat_days=10)])
    assert "no-sit" not in codes
    assert "no-uat" not in codes


def test_thin_design_ratio_flagged() -> None:
    # design 5 / build 100 = 5% < 8%
    assert "thin-design" in _codes([_phase(design=5, build=100)])


def test_thin_qa_ratio_flagged() -> None:
    # qa 10 / build 100 = 10% < 15%
    assert "thin-qa" in _codes([_phase(qa=10, build=100)])


def test_quality_named_stream_counts_as_qa() -> None:
    # 3.Quality is a test stream (is_qa_stream): qa 20 / build 100 = 20% >= 15%
    assert "thin-qa" not in _codes([_phase(qa=20, build=100, qa_stream="3.Quality")])


def test_heavy_overhead_ratio_flagged() -> None:
    # overhead 30 / build 100 = 30% > 25%
    assert "heavy-overhead" in _codes([_phase(overhead=30, build=100)])


def test_ratios_healthy_not_flagged() -> None:
    codes = _codes([_phase(design=20, qa=20, build=100, overhead=10)])
    assert {"thin-design", "thin-qa", "heavy-overhead"}.isdisjoint(codes)


def test_zero_build_skips_ratio_rules() -> None:
    # No build effort: ratios are undefined and must not divide-by-zero or fire.
    codes = _codes([_phase(design=0, qa=0, build=0)])
    assert {"thin-design", "thin-qa", "heavy-overhead"}.isdisjoint(codes)


def test_suggestions_aggregate_across_phases_naming_all() -> None:
    result = analyze_delivery_risks(
        [_phase("P1", design_lead_days=0), _phase("P2", design_lead_days=0)]
    )
    lead = [s for s in result if s.code == "zero-design-lead"]
    assert len(lead) == 1  # one suggestion, not one per phase
    assert "P1" in lead[0].detail and "P2" in lead[0].detail


def _alloc(monthly: list[float], label: str = "Dev") -> ResourceAllocation:
    return ResourceAllocation(label=label, monthly=monthly)


def test_off_grid_allocation_flagged() -> None:
    # 3 and 7 are not multiples of 5.
    codes = _codes([_phase(allocations=[_alloc([5, 3, 7, 10])])])
    assert "off-grid-allocation" in codes


def test_on_grid_allocation_not_flagged() -> None:
    codes = _codes([_phase(allocations=[_alloc([5, 10, 15, 20, 0])])])
    assert "off-grid-allocation" not in codes


def test_oscillating_allocation_flagged() -> None:
    # up, down, up = two reversals.
    codes = _codes([_phase(allocations=[_alloc([10, 20, 10, 20])])])
    assert "oscillating-allocation" in codes


def test_ramp_up_then_down_not_flagged_as_oscillating() -> None:
    codes = _codes([_phase(allocations=[_alloc([5, 10, 20, 10, 5])])])
    assert "oscillating-allocation" not in codes


def test_monotonic_ramps_not_flagged_as_oscillating() -> None:
    up = _codes([_phase(allocations=[_alloc([5, 10, 15, 20])])])
    down = _codes([_phase(allocations=[_alloc([20, 15, 10, 5])])])
    assert "oscillating-allocation" not in up
    assert "oscillating-allocation" not in down


def test_leading_trailing_zeros_ignored_for_oscillation() -> None:
    # A member who joins late and leaves early still ramps cleanly.
    codes = _codes([_phase(allocations=[_alloc([0, 0, 10, 20, 10, 0])])])
    assert "oscillating-allocation" not in codes


def test_milestone_cluster_flagged_at_threshold() -> None:
    result = analyze_delivery_risks([_phase()], milestones_by_month={"P1-M3": 3})
    assert "milestone-cluster" in {s.code for s in result}


def test_milestone_cluster_not_flagged_below_threshold() -> None:
    result = analyze_delivery_risks([_phase()], milestones_by_month={"P1-M3": 2})
    assert "milestone-cluster" not in {s.code for s in result}


def test_no_roadmap_means_no_milestone_suggestion() -> None:
    result = analyze_delivery_risks([_phase()], milestones_by_month=None)
    assert "milestone-cluster" not in {s.code for s in result}


@intent("INT-ESTIMATEKIT-011")
def test_all_suggestions_are_advisory_warnings() -> None:
    """INT-ESTIMATEKIT-011: every finding is an advisory suggestion, never a
    pass/fail check — the analyzer only ever emits AuditSuggestion warnings."""
    result = analyze_delivery_risks(
        [
            _phase(
                design_lead_days=0,
                lag_pct=0,
                sit_days=0,
                uat_days=0,
                design=1,
                qa=1,
                allocations=[_alloc([3, 10, 3])],
            )
        ]
    )
    assert result, "expected suggestions for a risk-laden phase"
    assert all(s.severity == "warning" for s in result)
    assert all(
        s.category in {"scheduling", "coverage", "ratios", "allocation"} for s in result
    )
