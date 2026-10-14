"""Tests for the All-phases month-order check.

Focus: the lifecycle / merged views intentionally overflow past the resourced
months for the testing tail, labelling those columns with the ``X-`` pseudo
phase. The check must allow that band while still rejecting a genuinely unknown
phase column (a truly stale roadmap).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.roadmap.conftest import check_all_phases_month_order


def _project(tmp_path: Path, *phase_ids: str) -> Path:
    """A minimal project root carrying only the phase-definitions file."""
    req = tmp_path / "data" / "requirements"
    req.mkdir(parents=True)
    lines = ["Phase ID\tPhase", *[f"{pid}\tPhase {pid[1:]}" for pid in phase_ids]]
    (req / "02-phases.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


def _row(*month_cols: str) -> dict[str, str]:
    """A lifecycle data row whose month columns are the given headers."""
    row = {"Category": "Objectives", "Effort (MD)": "7", "Milestone": "done"}
    row.update(dict.fromkeys(month_cols, ""))
    return row


class TestLifecycleOverflow:
    """The ``X-`` testing-tail overflow band is allowed; unknown phases are not."""

    def test_x_overflow_tail_is_allowed(self, tmp_path: Path) -> None:
        root = _project(tmp_path, "P1", "P2")
        rows = [_row("P1-M1", "P1-M2", "P2-M1", "X-M8")]
        # Must not raise: X- is the intentional testing-tail overflow band.
        check_all_phases_month_order(
            root / "Roadmap-LifecycleAll.tsv", rows, root, view="lifecycle",
        )

    def test_genuinely_unknown_phase_still_fails(self, tmp_path: Path) -> None:
        root = _project(tmp_path, "P1", "P2")
        rows = [_row("P1-M1", "P9-M1")]
        with pytest.raises(AssertionError, match="P9"):
            check_all_phases_month_order(
                root / "Roadmap-LifecycleAll.tsv", rows, root, view="lifecycle",
            )
