"""TSV header validation: empty headers, whitespace, well-known schemas."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.phases import discover_phases
from auditor.project import get_data_file
from auditor.tsv import read_tsv_raw

logger = logging.getLogger(__name__)

# ── Expected header prefixes for well-known file types ──────────────────────

EXPECTED_HEADERS: dict[str, list[str]] = {
    "requirements/01-brd.tsv": ["Category", "Req ID", "Description"],
    "requirements/02-phases.tsv": ["Phase", "Phase ID", "Name"],
    "requirements/03-matrix.tsv": ["Category", "Req ID", "Description"],
    "assumptions/00-confidence.tsv": ["Confidence"],
    "assumptions/01-impact.tsv": ["Impact"],
    "assumptions/02-assumptions.tsv": ["Group", "Assumption ID"],
    "architecture/00-guidelines.tsv": ["Group"],
}

ACTIVITIES_BUILD_HEADERS = ["Group", "Activity ID", "Activity", "Req IDs", "Effort (MD)"]
ACTIVITIES_PROJECT_HEADERS = ["Stream", "Activity Group", "Effort (MD)"]
ACTIVITIES_RESOURCE_HEADERS = ["Stream", "Profile", "Rate Day"]
ACTIVITIES_CONFIG_HEADERS = ["Parameter", "Value"]
SLIDES_EXECUTIVE_SUMMARY_HEADERS = ["Section", "Key", "Value"]
SLIDES_NOTES_HEADERS = ["Slide", "Position", "Text"]


def _all_tsv_files(project_root: Path) -> list[Path]:
    data_dir = project_root / "data"
    if not data_dir.exists():
        return []
    return sorted(data_dir.rglob("*.tsv"))


def test_no_empty_headers(project_root: Path) -> None:
    """No TSV has empty column names."""
    failures: list[str] = []
    for tsv in _all_tsv_files(project_root):
        rows = read_tsv_raw(tsv)
        if not rows:
            continue
        for i, col in enumerate(rows[0]):
            if not col.strip():
                failures.append(f"{tsv.name}: empty header at column {i}")

    assert not failures, "Empty headers:\n  " + "\n  ".join(failures)


def test_no_trailing_whitespace_in_headers(project_root: Path) -> None:
    """No TSV has leading/trailing whitespace in column names."""
    failures: list[str] = []
    for tsv in _all_tsv_files(project_root):
        rows = read_tsv_raw(tsv)
        if not rows:
            continue
        for col in rows[0]:
            if col != col.strip():
                failures.append(f"{tsv.name}: '{col}' has whitespace")

    assert not failures, "Whitespace in headers:\n  " + "\n  ".join(failures)


def test_well_known_files_have_expected_headers(project_root: Path) -> None:
    """Well-known TSV files start with expected header columns."""
    failures: list[str] = []
    for rel_path, expected_prefix in EXPECTED_HEADERS.items():
        subdir, filename = rel_path.split("/", 1)
        path = get_data_file(project_root, subdir, filename)
        if not path.exists():
            continue
        rows = read_tsv_raw(path)
        if not rows:
            failures.append(f"{filename}: empty file")
            continue
        actual = rows[0][: len(expected_prefix)]
        for i, (exp, act) in enumerate(zip(expected_prefix, actual, strict=False)):
            if exp != act.strip():
                failures.append(
                    f"{filename}: col {i} expected '{exp}', got '{act.strip()}'"
                )

    logger.info("Checked %d well-known headers", len(EXPECTED_HEADERS))
    assert not failures, "Header mismatches:\n  " + "\n  ".join(failures)


def _check_phase_headers(
    project_root: Path,
    subdir: str,
    file_suffix: str,
    expected_headers: list[str],
    label: str,
) -> None:
    """Shared logic for checking the headers of a per-phase file kind."""
    phases = discover_phases(project_root)
    failures: list[str] = []
    for ph in phases:
        path = get_data_file(
            project_root, subdir, f"{ph['phase_id']}-{file_suffix}.tsv"
        )
        if not path.exists():
            continue
        rows = read_tsv_raw(path)
        if not rows:
            continue
        actual = rows[0][: len(expected_headers)]
        for i, (exp, act) in enumerate(zip(expected_headers, actual, strict=False)):
            if exp != act.strip():
                failures.append(
                    f"{path.name}: col {i} expected '{exp}', got '{act.strip()}'"
                )

    assert not failures, f"{label} header mismatches:\n  " + "\n  ".join(failures)


def test_activity_build_files_have_expected_headers(project_root: Path) -> None:
    """All activities/*-build.tsv files have the expected header columns."""
    _check_phase_headers(
        project_root, "activities", "build", ACTIVITIES_BUILD_HEADERS, "Build",
    )


def test_activity_project_files_have_expected_headers(project_root: Path) -> None:
    """All activities/*-project.tsv files have the expected header columns."""
    _check_phase_headers(
        project_root, "activities", "project", ACTIVITIES_PROJECT_HEADERS, "Project",
    )


def test_activity_resource_files_have_expected_headers(project_root: Path) -> None:
    """All activities/*-resource.tsv files have the expected header columns."""
    _check_phase_headers(
        project_root, "activities", "resource", ACTIVITIES_RESOURCE_HEADERS, "Resource",
    )


def test_activity_config_files_have_expected_headers(project_root: Path) -> None:
    """All activities/*-config.tsv files have the expected header columns."""
    _check_phase_headers(
        project_root, "activities", "config", ACTIVITIES_CONFIG_HEADERS, "Config",
    )


def test_slides_executive_summary_files_have_expected_headers(project_root: Path) -> None:
    """All slides/*-executive-summary.tsv files have the expected header columns."""
    _check_phase_headers(
        project_root,
        "slides",
        "executive-summary",
        SLIDES_EXECUTIVE_SUMMARY_HEADERS,
        "Executive summary",
    )


def test_slides_notes_files_have_expected_headers(project_root: Path) -> None:
    """All slides/*-notes.tsv files have the expected header columns."""
    _check_phase_headers(project_root, "slides", "notes", SLIDES_NOTES_HEADERS, "Notes")
