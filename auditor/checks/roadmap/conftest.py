"""Roadmap validation helpers, constants, and phase-file parametrization.

Validates generated roadmap output across four views:
  View 1 — Resource Timeline
  View 2 — Activity Group Timeline
  View 3 — Build Zoom-In
  View 4 — Feature Lifecycle
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from auditor.phases import discover_phases, missing_phases_file, phase_discovery_problem
from auditor.project import try_resolve_project_root

# ── Constants ───────────────────────────────────────────────────────────────

ROADMAP_DIR_NAME = "output/roadmap"

# View 3 markers
BUILD_ACTIVE = {"·"}
BUILD_MILESTONE = {"◆"}

# View 4 (Lifecycle) markers
LIFECYCLE_DESIGN = {"D"}
LIFECYCLE_BUILD = {"·"}
LIFECYCLE_BUILD_MILESTONE = {"◆"}
LIFECYCLE_TEST = {"T"}
LIFECYCLE_TEST_MILESTONE = {"▲"}
LIFECYCLE_ALL_ACTIVE = {"D", "·", "◆", "T", "▲"}

# The lifecycle and merged "All" views intentionally overflow past the resourced
# months to show the testing tail; those overflow columns are labelled with this
# pseudo-phase prefix (``X-M8``) by the generators (roadmap_merger / view_mergers,
# and handled by the slide renderer's labels). It is not a real phase, so the
# month-order check allows it and sorts it after every real phase.
LIFECYCLE_OVERFLOW_PHASE = "X"


# ── I/O helpers ─────────────────────────────────────────────────────────────

def roadmap_dir(project_root: Path) -> Path:
    """Return the ``output/roadmap/`` directory path."""
    return project_root / ROADMAP_DIR_NAME


# ── Row helpers ─────────────────────────────────────────────────────────────

def month_cols_build(rows: list[dict[str, str]]) -> list[str]:
    """Extract month-column names from a Build TSV header."""
    if not rows:
        return []
    keys = list(rows[0].keys())
    if "Milestone" in keys:
        start = keys.index("Milestone") + 1
    elif "Effort (MD)" in keys:
        start = keys.index("Effort (MD)") + 1
    else:
        start = 1
    return keys[start:]


def month_cols_lifecycle(rows: list[dict[str, str]]) -> list[str]:
    """Extract month-column names from a Lifecycle TSV header."""
    return month_cols_build(rows)


def month_cols_resource(rows: list[dict[str, str]]) -> list[str]:
    """Extract month-column names from a Resource TSV header."""
    if not rows:
        return []
    keys = list(rows[0].keys())
    start = keys.index("Total (MD)") + 1 if "Total (MD)" in keys else 1
    return keys[start:]


def month_cols_activity_group(rows: list[dict[str, str]]) -> list[str]:
    """Extract month-column names from an Activity Group TSV header."""
    if not rows:
        return []
    keys = list(rows[0].keys())
    start = keys.index("Milestone") + 1 if "Milestone" in keys else 1
    return keys[start:]


def is_footer(row: dict[str, str], name_col: str = "Category") -> bool:
    """True when a row is a footer (empty name column)."""
    return not row.get(name_col, "").strip()


def data_rows(
    rows: list[dict[str, str]], name_col: str = "Category",
) -> list[dict[str, str]]:
    """Return only non-footer rows."""
    return [r for r in rows if not is_footer(r, name_col)]


# ── Phase-file discovery ────────────────────────────────────────────────────

_PROJECT_ROOT, _ = try_resolve_project_root()


def get_phase_files(project_root: Path) -> list[dict]:
    """Discover per-phase roadmap output file paths (all 4 views)."""
    phases = discover_phases(project_root)
    rd = roadmap_dir(project_root)
    result = []
    for ph in phases:
        pid = ph["phase_id"]
        result.append({
            "name": pid,
            "resource": rd / f"Roadmap-Resource{pid}.tsv",
            "activity_group": rd / f"Roadmap-ActivityGroup{pid}.tsv",
            "build": rd / f"Roadmap-Build{pid}.tsv",
            "lifecycle": rd / f"Roadmap-Lifecycle{pid}.tsv",
            "config": ph["config_file"],
        })
    return result


def get_all_files(project_root: Path) -> dict[str, Path]:
    """Return All-phases roadmap file paths (all 4 views)."""
    rd = roadmap_dir(project_root)
    return {
        "resource": rd / "Roadmap-ResourceAll.tsv",
        "activity_group": rd / "Roadmap-ActivityGroupAll.tsv",
        "build": rd / "Roadmap-BuildAll.tsv",
        "lifecycle": rd / "Roadmap-LifecycleAll.tsv",
    }


# ── Validation: View 1 Resource ────────────────────────────────────────────

def check_resource_totals(path: Path, rows: list[dict[str, str]]) -> None:
    """Validate the TOTAL footer row sums match column sums."""
    cols = month_cols_resource(rows)
    stream_rows = [
        r for r in rows
        if r.get("Stream", "").strip() and r["Stream"].strip() != "TOTAL"
    ]
    footer_rows = [r for r in rows if r.get("Stream", "").strip() == "TOTAL"]
    if not footer_rows:
        return
    footer = footer_rows[0]
    failures: list[str] = []
    for col in cols:
        expected = sum(float(r.get(col, "0").strip() or "0") for r in stream_rows)
        actual_str = footer.get(col, "").strip()
        try:
            actual = float(actual_str)
        except (ValueError, TypeError):
            actual = -1
        if abs(actual - expected) > 1:
            failures.append(f"{col}: footer={actual}, sum={expected}")
    assert not failures, (
        f"{path.name} resource total mismatch:\n  " + "\n  ".join(failures)
    )


def check_resource_numeric(path: Path, rows: list[dict[str, str]]) -> None:
    """Validate all resource capacity values are numeric."""
    cols = month_cols_resource(rows)
    failures: list[str] = []
    for row in rows:
        stream = row.get("Stream", "").strip()
        if not stream:
            continue
        for col in cols:
            val = row.get(col, "").strip()
            if not val:
                continue
            try:
                float(val)
            except ValueError:
                failures.append(f"{stream}/{col}: '{val}' not numeric")
    assert not failures, (
        f"{path.name} non-numeric:\n  " + "\n  ".join(failures)
    )


# ── Validation: View 2 Activity Groups ─────────────────────────────────────

def check_activity_group_contiguous(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate no gaps in activity group marker blocks."""
    cols = month_cols_activity_group(rows)
    ag_rows = [r for r in rows if r.get("Activity Group", "").strip()]
    failures: list[str] = []
    active_marks = {"·", "◆"}
    for row in ag_rows:
        group = row.get("Activity Group", "").strip()
        marks = [1 if row.get(c, "").strip() in active_marks else 0 for c in cols]
        active_idxs = [i for i, m in enumerate(marks) if m]
        if len(active_idxs) <= 1:
            continue
        span = range(active_idxs[0], active_idxs[-1] + 1)
        gaps = [cols[i] for i in span if marks[i] == 0]
        if gaps:
            failures.append(f"{group}: gap in {', '.join(gaps)}")
    assert not failures, (
        f"{path.name} non-contiguous:\n  " + "\n  ".join(failures)
    )


def check_activity_group_milestone_at_end(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate ◆ is at end of each activity group's active block."""
    cols = month_cols_activity_group(rows)
    ag_rows = [r for r in rows if r.get("Activity Group", "").strip()]
    active_marks = {"·", "◆"}
    failures: list[str] = []
    for row in ag_rows:
        group = row.get("Activity Group", "").strip()
        active_cols = [
            (c, row.get(c, "").strip())
            for c in cols
            if row.get(c, "").strip() in active_marks
        ]
        if not active_cols:
            continue
        _, last_val = active_cols[-1]
        if last_val != "◆":
            failures.append(f"{group}: last active has '{last_val}', expected '◆'")
    assert not failures, (
        f"{path.name} milestone not at end:\n  " + "\n  ".join(failures)
    )


# ── Validation: View 3 Build ───────────────────────────────────────────────

def check_build_contiguous(path: Path, rows: list[dict[str, str]]) -> None:
    """Validate no gaps in build marker blocks."""
    cols = month_cols_build(rows)
    cats = data_rows(rows)
    marks_set = BUILD_ACTIVE | BUILD_MILESTONE
    failures: list[str] = []
    for row in cats:
        cat = row.get("Category", "").strip()
        marks = [1 if row.get(c, "").strip() in marks_set else 0 for c in cols]
        active_idxs = [i for i, m in enumerate(marks) if m]
        if len(active_idxs) <= 1:
            continue
        span = range(active_idxs[0], active_idxs[-1] + 1)
        gaps = [cols[i] for i in span if marks[i] == 0]
        if gaps:
            failures.append(f"{cat}: gap in {', '.join(gaps)}")
    assert not failures, (
        f"{path.name} non-contiguous:\n  " + "\n  ".join(failures)
    )


def check_build_milestone_at_end(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate ◆ is at end of each category's active block in Build view."""
    cols = month_cols_build(rows)
    cats = data_rows(rows)
    active_marks = BUILD_ACTIVE | BUILD_MILESTONE
    failures: list[str] = []
    for row in cats:
        cat = row.get("Category", "").strip()
        active_cols = [
            (c, row.get(c, "").strip())
            for c in cols
            if row.get(c, "").strip() in active_marks
        ]
        if not active_cols:
            continue
        _, last_val = active_cols[-1]
        if last_val != "◆":
            failures.append(f"{cat}: last active has '{last_val}', expected '◆'")
    assert not failures, (
        f"{path.name} milestone not at end:\n  " + "\n  ".join(failures)
    )


def check_build_footer_counts(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate footer milestone counts match counted ◆ markers."""
    footers = [r for r in rows if is_footer(r)]
    if not footers:
        return
    footer = footers[-1]
    cats = data_rows(rows)
    cols = month_cols_build(rows)
    failures: list[str] = []
    for col in cols:
        expected = sum(1 for r in cats if r.get(col, "").strip() in BUILD_MILESTONE)
        actual_str = footer.get(col, "").strip()
        if not actual_str:
            continue
        try:
            actual = int(actual_str)
        except ValueError:
            actual = -1
        if actual != expected:
            failures.append(f"{col}: footer={actual}, counted={expected}")
    assert not failures, (
        f"{path.name} footer mismatch:\n  " + "\n  ".join(failures)
    )


def check_effort_numeric(path: Path, rows: list[dict[str, str]]) -> None:
    """Validate all Effort (MD) values are numeric."""
    cats = data_rows(rows)
    failures: list[str] = []
    for row in cats:
        cat = row.get("Category", "").strip()
        effort = row.get("Effort (MD)", "").strip()
        if not effort:
            failures.append(f"{cat}: empty Effort")
            continue
        cleaned = effort.rstrip("d").strip()
        try:
            float(cleaned)
        except ValueError:
            failures.append(f"{cat}: '{effort}' not numeric")
    assert not failures, (
        f"{path.name} effort issues:\n  " + "\n  ".join(failures)
    )


# ── Validation: View 4 Lifecycle ───────────────────────────────────────────

def check_lifecycle_contiguous(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate no gaps in lifecycle marker blocks (D..·..◆..T..▲)."""
    cols = month_cols_lifecycle(rows)
    cats = data_rows(rows)
    failures: list[str] = []
    for row in cats:
        cat = row.get("Category", "").strip()
        marks = [
            1 if row.get(c, "").strip() in LIFECYCLE_ALL_ACTIVE else 0
            for c in cols
        ]
        active_idxs = [i for i, m in enumerate(marks) if m]
        if len(active_idxs) <= 1:
            continue
        span = range(active_idxs[0], active_idxs[-1] + 1)
        gaps = [cols[i] for i in span if marks[i] == 0]
        if gaps:
            failures.append(f"{cat}: gap in {', '.join(gaps)}")
    assert not failures, (
        f"{path.name} non-contiguous:\n  " + "\n  ".join(failures)
    )


def check_lifecycle_design_before_build(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate D markers precede ·/◆ markers in Lifecycle view."""
    cols = month_cols_lifecycle(rows)
    cats = data_rows(rows)
    failures: list[str] = []
    build_marks = (
        LIFECYCLE_BUILD | LIFECYCLE_BUILD_MILESTONE
        | LIFECYCLE_TEST | LIFECYCLE_TEST_MILESTONE
    )
    for row in cats:
        cat = row.get("Category", "").strip()
        build_started = False
        for c in cols:
            val = row.get(c, "").strip()
            if val in build_marks:
                build_started = True
            elif val == "D" and build_started:
                failures.append(f"{cat}: D at {c} after build started")
    assert not failures, (
        f"{path.name} design after build:\n  " + "\n  ".join(failures)
    )


def check_lifecycle_build_before_test(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate build markers (·/◆) precede test markers (T/▲)."""
    cols = month_cols_lifecycle(rows)
    cats = data_rows(rows)
    failures: list[str] = []
    test_marks = LIFECYCLE_TEST | LIFECYCLE_TEST_MILESTONE
    build_marks = LIFECYCLE_BUILD | LIFECYCLE_BUILD_MILESTONE | LIFECYCLE_DESIGN
    for row in cats:
        cat = row.get("Category", "").strip()
        test_started = False
        for c in cols:
            val = row.get(c, "").strip()
            if val in test_marks:
                test_started = True
            elif val in build_marks and test_started:
                failures.append(f"{cat}: build/design at {c} after test started")
    assert not failures, (
        f"{path.name} build after test:\n  " + "\n  ".join(failures)
    )


def check_lifecycle_build_milestone_at_end(
    path: Path, rows: list[dict[str, str]], *, integrated_testing: bool = False,
) -> None:
    """Validate the build section ends on its milestone.

    The milestone is ◆. With SIT and UAT both 0 (*integrated_testing*, testing
    integrated with the build) the generator draws no test window, and when the
    phase carries testing effort it ends the build on ▲ instead, acceptance
    completing with the build: either mark may end it then.
    """
    cols = month_cols_lifecycle(rows)
    cats = data_rows(rows)
    build_marks = LIFECYCLE_BUILD | LIFECYCLE_BUILD_MILESTONE
    end_marks = set(LIFECYCLE_BUILD_MILESTONE)
    if integrated_testing:
        build_marks = build_marks | LIFECYCLE_TEST_MILESTONE
        end_marks |= LIFECYCLE_TEST_MILESTONE
    failures: list[str] = []
    for row in cats:
        cat = row.get("Category", "").strip()
        cells = [row.get(c, "").strip() for c in cols]
        build_vals = [v for v in cells if v in build_marks]
        if not build_vals:
            continue
        last_val = build_vals[-1]
        if last_val not in end_marks:
            expected = " or ".join(f"'{m}'" for m in sorted(end_marks))
            failures.append(
                f"{cat}: last build marker is '{last_val}', expected {expected}",
            )
    assert not failures, (
        f"{path.name} build milestone not at end:\n  " + "\n  ".join(failures)
    )


def check_lifecycle_footer_counts(
    path: Path, rows: list[dict[str, str]],
) -> None:
    """Validate footer milestone counts match counted ◆ markers."""
    footers = [r for r in rows if is_footer(r)]
    if not footers:
        return
    footer = footers[-1]
    cats = data_rows(rows)
    cols = month_cols_lifecycle(rows)
    failures: list[str] = []
    for col in cols:
        expected = sum(1 for r in cats if r.get(col, "").strip() == "◆")
        actual_str = footer.get(col, "").strip()
        if not actual_str:
            continue
        try:
            actual = int(actual_str)
        except ValueError:
            actual = -1
        if actual != expected:
            failures.append(f"{col}: footer={actual}, counted={expected}")
    assert not failures, (
        f"{path.name} footer mismatch:\n  " + "\n  ".join(failures)
    )


# ── Validation: All-phases month ordering ──────────────────────────────────

def check_all_phases_month_order(
    path: Path,
    rows: list[dict[str, str]],
    project_root: Path,
    view: str = "build",
) -> None:
    """Validate month columns are in correct phase/month order."""
    if view == "resource":
        cols = month_cols_resource(rows)
    elif view == "activity_group":
        cols = month_cols_activity_group(rows)
    else:
        cols = month_cols_build(rows)

    problem = missing_phases_file(project_root)
    if problem:
        pytest.skip(problem)

    phase_order: dict[str, int] = {}
    try:
        phases = discover_phases(project_root)
        for i, ph in enumerate(phases):
            phase_order[ph["phase_id"]] = i
    except Exception:
        pass

    if not phase_order:
        return

    unknown_phases: set[str] = set()
    for col in cols:
        m = re.match(r"([A-Za-z0-9]+)-M(\d+)", col)
        if m:
            phase_key = m.group(1)
            if phase_key not in phase_order and phase_key != LIFECYCLE_OVERFLOW_PHASE:
                unknown_phases.add(phase_key)

    assert not unknown_phases, (
        f"{path.name} has phase columns {unknown_phases} not matching "
        f"current phases {set(phase_order.keys())} — regenerate roadmaps"
    )

    failures: list[str] = []
    prev_rank = -1
    prev_month = 0
    for col in cols:
        m = re.match(r"([A-Za-z0-9]+)-M(\d+)", col)
        if not m:
            failures.append(f"Column '{col}' doesn't match pattern")
            continue
        phase_key, month = m.group(1), int(m.group(2))
        # The overflow band sorts after every real phase (it is the tail).
        if phase_key == LIFECYCLE_OVERFLOW_PHASE:
            rank = len(phase_order)
        else:
            rank = phase_order.get(phase_key, -1)
        if rank < prev_rank:
            failures.append(f"Column '{col}' goes backwards")
        elif rank == prev_rank and month <= prev_month:
            failures.append(f"Column '{col}' month not increasing")
        prev_rank = rank
        prev_month = month if rank == prev_rank else 0
        if rank != prev_rank:
            prev_rank = rank
            prev_month = month

    assert not failures, (
        f"{path.name} month order:\n  " + "\n  ".join(failures)
    )


# ── pytest parametrization ──────────────────────────────────────────────────

def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize the ``phase_files`` fixture from discovered phases.

    When phase discovery is impossible (no project, or the phase-definitions
    file is missing), each per-phase roadmap check is skipped with a reason
    naming the missing file; roadmap output is validated against that input.
    """
    if "phase_files" not in metafunc.fixturenames:
        return
    problem = phase_discovery_problem()
    if problem:
        metafunc.parametrize(
            "phase_files",
            [pytest.param({}, marks=pytest.mark.skip(reason=problem))],
            ids=["phases-missing"],
        )
        return
    pf = get_phase_files(_PROJECT_ROOT)
    selected = metafunc.config.getoption("phase")
    if selected is not None:
        pf = [p for p in pf if p["name"] == selected]
    metafunc.parametrize("phase_files", pf, ids=[p["name"] for p in pf])
