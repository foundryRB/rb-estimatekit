"""Tests for the QA window check on a scaffold-shaped project.

The scaffold names its test stream 3.Test. The QA window check reads the test
streams by the shared rule (``is_qa_stream``), so the scaffold's test effort is
measured: test capacity booked before the QA start month does not cover it.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import engine
from auditor.checks.activity import test_timeline as timeline
from auditor.phases import discover_phases
from engine.adapters.outbound.persistence.file_template_repository import (
    FileTemplateRepository,
)

_TEMPLATES_DIR = Path(engine.__file__).resolve().parent.parent / "templates"
_SCAFFOLD_TEST_STREAM = "3.Test"


def _scaffold_p1(tmp_path: Path) -> dict[str, Any]:
    """Scaffold the templates into a project root and return its P1 phase."""
    FileTemplateRepository(_TEMPLATES_DIR).scaffold_to(tmp_path / "data")
    return next(p for p in discover_phases(tmp_path) if p["phase_id"] == "P1")


def _rewrite_rows(
    path: Path, first_cell: str, rewrite: Callable[[list[str]], list[str]]
) -> None:
    """Rewrite each TSV data row whose first cell is *first_cell*."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out = [lines[0]]
    for line in lines[1:]:
        cells = line.split("\t")
        out.append("\t".join(rewrite(cells)) if cells[0] == first_cell else line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _set_testing_lag(phase: dict[str, Any], pct: int) -> None:
    _rewrite_rows(phase["config_file"], "Testing Lag", lambda c: [c[0], str(pct), *c[2:]])


def _book_test_capacity_in_m1(phase: dict[str, Any]) -> None:
    """Move the test stream's capacity into M1 (20 md, the month's ceiling)."""

    def rewrite(cells: list[str]) -> list[str]:
        months = len(cells) - 3
        return [*cells[:3], "20", *["0"] * (months - 1)]

    _rewrite_rows(phase["resource_file"], _SCAFFOLD_TEST_STREAM, rewrite)


def _rename_test_stream(phase: dict[str, Any], name: str) -> None:
    for key in ("project_file", "resource_file"):
        _rewrite_rows(phase[key], _SCAFFOLD_TEST_STREAM, lambda c: [name, *c[1:]])


class TestScaffoldTestStream:
    """The QA window check measures the scaffold's 3.Test effort."""

    def test_scaffold_passes_as_shipped(self, tmp_path: Path) -> None:
        phase = _scaffold_p1(tmp_path)
        timeline.test_qa_timeline_feasibility(phase)

    @pytest.mark.parametrize("stream", [_SCAFFOLD_TEST_STREAM, "3.Quality"])
    def test_capacity_before_qa_start_fails(self, tmp_path: Path, stream: str) -> None:
        """Testing Lag 50 starts QA in M3 of the four-month P1; M1 capacity misses it."""
        phase = _scaffold_p1(tmp_path)
        _set_testing_lag(phase, 50)
        _book_test_capacity_in_m1(phase)
        if stream != _SCAFFOLD_TEST_STREAM:
            _rename_test_stream(phase, stream)
        with pytest.raises(AssertionError, match=r"QA capacity from M3 \(0\) < QA effort \(20\)"):
            timeline.test_qa_timeline_feasibility(phase)

    def test_capacity_from_qa_start_passes(self, tmp_path: Path) -> None:
        """The scaffold's own booking (10 md in M3, 15 in M4) covers 20 md from M3."""
        phase = _scaffold_p1(tmp_path)
        _set_testing_lag(phase, 50)
        timeline.test_qa_timeline_feasibility(phase)
