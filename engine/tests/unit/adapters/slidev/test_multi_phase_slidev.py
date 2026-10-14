"""Regression tests for Slidev rendering with more than the four conventional phases.

Ticket #6: a project with five phases (``Demo``, ``P1``, ``P2A``, ``P2B``, ``P3``)
must render each phase distinctly. These tests exercise the three places that
previously assumed exactly ``Demo/P1/P2/P3``:

  1. ``vrom._phase_style`` — unknown phases must cycle to distinct colours,
     never collapse to a single grey.
  2. ``roadmap_slides.labels`` — phase detection/stripping must use the
     project's actual phase ids, matched longest-first so ``P2`` cannot
     swallow ``P2A``.
  3. ``roadmap_slides.phase_headers.compute_col_phases`` — column-to-phase
     mapping must attribute ``P2A``/``P2B`` months to their own phase.
"""

from __future__ import annotations

from engine.adapters.outbound.slidev.roadmap_slides.labels import (
    detect_phase_from_label,
    strip_month_prefix,
    strip_row_phase_prefix,
)
from engine.adapters.outbound.slidev.roadmap_slides.phase_headers import (
    compute_col_phases,
)
from engine.adapters.outbound.slidev.vrom import _phase_style

FIVE_PHASES = ["Demo", "P1", "P2A", "P2B", "P3"]


class TestPhaseStyle:
    """vrom colour/class assignment for extra phases."""

    def test_known_phases_keep_their_mapped_colour(self) -> None:
        assert _phase_style("P1", 1)[0] == "#00a86b"

    def test_p1_carries_the_brand_primary_everywhere(self) -> None:
        # project.yaml's primary_color is the accent of P1 on every slide (effort, VROM,
        # roadmap); the other phases keep their neutral accents (estimatekit#14).
        from engine.adapters.outbound.slidev.effort import _phase_css
        from engine.adapters.outbound.slidev.roadmap_slides.colors import phase_color

        assert _phase_style("P1", 1, "#F26522")[0] == "#F26522"
        assert _phase_css("P1", 1, "#F26522")[1] == "#F26522"
        assert phase_color("P1", "#F26522") == "#F26522"
        assert phase_color("Demo", "#F26522") == "#1976D2"
        assert _phase_style("P2", 2, "#F26522")[0] == "#333333"

    def test_unknown_phases_get_distinct_colours(self) -> None:
        # P2A and P2B are unknown to the four-phase colour map; they must not
        # both fall back to the same grey.
        color_p2a, css_p2a = _phase_style("P2A", 2)
        color_p2b, css_p2b = _phase_style("P2B", 3)
        assert color_p2a != color_p2b
        assert css_p2a != css_p2b
        assert color_p2a != "#666" and color_p2b != "#666"


class TestLabelParsing:
    """Longest-first phase matching against the project's own phase ids."""

    def test_detects_extra_phase(self) -> None:
        assert detect_phase_from_label("P2A-M1", FIVE_PHASES) == "P2A"
        assert detect_phase_from_label("P2B-M3", FIVE_PHASES) == "P2B"

    def test_longest_first_p2_does_not_swallow_p2a(self) -> None:
        # With P2 tried before P2A, "P2A-M1" would wrongly detect as "P2".
        assert detect_phase_from_label("P2A-M1", FIVE_PHASES) == "P2A"

    def test_strip_month_prefix_uses_full_phase_id(self) -> None:
        assert strip_month_prefix("P2A-M1", FIVE_PHASES) == "M1"
        assert strip_month_prefix("P2B-M1", FIVE_PHASES) == "M1"

    def test_strip_month_prefix_keeps_testing_tail(self) -> None:
        assert strip_month_prefix("X-M16", FIVE_PHASES) == "+1"

    def test_strip_row_phase_prefix(self) -> None:
        assert strip_row_phase_prefix("P2A: Design Lead", FIVE_PHASES) == "Design Lead"

    def test_bare_month_label_has_no_phase(self) -> None:
        assert detect_phase_from_label("M4", FIVE_PHASES) == ""


class TestColumnPhases:
    """Column-to-phase attribution across a five-phase month sequence."""

    def test_p2a_and_p2b_columns_attributed_to_own_phase(self) -> None:
        labels = ["Demo-M1", "P1-M1", "P2A-M1", "P2B-M1", "P3-M1"]
        assert compute_col_phases(labels, FIVE_PHASES) == FIVE_PHASES

    def test_leading_unlabelled_columns_default_to_first_phase(self) -> None:
        labels = ["M1", "P1-M1"]
        assert compute_col_phases(labels, FIVE_PHASES) == ["Demo", "P1"]
