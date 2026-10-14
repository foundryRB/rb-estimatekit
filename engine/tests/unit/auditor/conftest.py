"""Synthetic project builder for the auditor's cross-file reference checks."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

_ASSUMPTIONS_HEADER = [
    "Group", "Assumption ID", "Assumption", "Short Title", "Confidence", "Impact", "Req IDs",
]


def _write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Write *rows* under *header* as a tab-separated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(header), *("\t".join(row) for row in rows)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def write_project(tmp_path: Path) -> Callable[..., Path]:
    """Build a project root holding the files the reference checks read.

    The defaults are a clean one-phase project: the matrix assigns AUTH-001
    and DASH-001 to Phase 1, the BRD holds the same IDs, P1 has one build
    activity per requirement, and the one assumption names All. Each keyword
    overrides one part: ``phases`` (id to name), ``requirements`` (Req ID to
    the phase names it is marked in), ``matrix_columns`` (the matrix's phase
    columns), ``brd`` (the BRD's Req IDs), ``builds`` (phase id to its build
    activities' Req IDs cells), and ``assumptions`` (Req IDs cells).
    """

    def write(
        *,
        phases: dict[str, str] | None = None,
        requirements: dict[str, list[str]] | None = None,
        matrix_columns: list[str] | None = None,
        brd: list[str] | None = None,
        builds: dict[str, list[str]] | None = None,
        assumptions: list[str] | None = None,
    ) -> Path:
        phases = phases or {"P1": "Phase 1"}
        requirements = requirements or {"AUTH-001": ["Phase 1"], "DASH-001": ["Phase 1"]}
        columns = list(phases.values()) if matrix_columns is None else matrix_columns
        brd_ids = list(requirements) if brd is None else brd
        if builds is None:
            builds = {
                pid: [rid for rid, marked in requirements.items() if name in marked]
                for pid, name in phases.items()
            }
        assumptions = ["All"] if assumptions is None else assumptions

        req_dir = tmp_path / "data" / "requirements"
        _write_tsv(
            req_dir / "02-phases.tsv",
            ["Phase", "Phase ID"],
            [[name, pid] for pid, name in phases.items()],
        )
        matrix_rows = [
            ["Core", rid, f"Requirement {rid}", *("✓" if c in marked else "" for c in columns), ""]
            for rid, marked in requirements.items()
        ]
        _write_tsv(
            req_dir / "03-matrix.tsv",
            ["Category", "Req ID", "Description", *columns, "Notes"],
            matrix_rows,
        )
        _write_tsv(
            req_dir / "01-brd.tsv",
            ["Category", "Req ID", "Description"],
            [["Core", rid, f"Requirement {rid}"] for rid in brd_ids],
        )
        for pid, cells in builds.items():
            _write_tsv(
                tmp_path / "data" / "activities" / f"{pid}-build.tsv",
                ["Group", "Activity ID", "Activity", "Req IDs", "Effort (MD)", "Description"],
                [
                    ["Core", f"{pid}-BUILD-{i:03d}", f"Activity {i}", cell, "5", ""]
                    for i, cell in enumerate(cells, start=1)
                ],
            )
        _write_tsv(
            tmp_path / "data" / "assumptions" / "02-assumptions.tsv",
            _ASSUMPTIONS_HEADER,
            [
                ["Platform", f"A-{i:03d}", f"Assumption {i}", f"Title {i}", "HIGH", "HIGH", cell]
                for i, cell in enumerate(assumptions, start=1)
            ],
        )
        return tmp_path

    return write
