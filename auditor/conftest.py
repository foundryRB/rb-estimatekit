"""Shared pytest fixtures and dynamic phase parametrization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from auditor.config import load_config
from auditor.phases import discover_phases, phase_discovery_problem
from auditor.project import try_resolve_project_root

_PROJECT_ROOT, _PROJECT_PROBLEM = try_resolve_project_root()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Absolute path to the active project instance."""
    if _PROJECT_ROOT is None:
        pytest.fail(_PROJECT_PROBLEM or "No project found.", pytrace=False)
    return _PROJECT_ROOT


@pytest.fixture(scope="session")
def config(project_root: Path) -> dict[str, Any]:
    """Loaded ``project.yaml`` configuration dict."""
    return load_config(project_root)


@pytest.fixture(scope="session")
def all_phases(project_root: Path) -> list[dict[str, Any]]:
    """All discovered phases (list of dicts)."""
    return discover_phases(project_root)


@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Path to the project's ``data/`` directory (root of all subdirectories)."""
    return project_root / "data"


@pytest.fixture
def phase(request: pytest.FixtureRequest) -> dict[str, Any]:
    """One discovered phase dict.

    Parametrized with the problem message (a string) when phase discovery is
    impossible; in that case the check fails, naming the missing file.
    """
    if isinstance(request.param, str):
        pytest.fail(request.param, pytrace=False)
    return request.param


def pytest_addoption(parser: pytest.Parser) -> None:
    """Select one phase while retaining shared project checks."""
    parser.addoption(
        "--phase", default=None, help="Audit one defined phase plus shared integrity checks"
    )


def pytest_configure(config: pytest.Config) -> None:
    """Reject an undefined selection even when running only shared checks."""
    selected = config.getoption("phase")
    if selected is not None and phase_discovery_problem() is None:
        defined = [p["phase_id"] for p in discover_phases(_PROJECT_ROOT)]
        if selected not in defined:
            raise pytest.UsageError(f"Phase not found: {selected!r}; defined: {', '.join(defined)}")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize the ``phase`` fixture from discovered phases.

    When phase discovery is impossible (no project, or the phase-definitions
    file is missing), each per-phase check fails with the problem message via
    the ``phase`` fixture instead of aborting collection.
    """
    if "phase" not in metafunc.fixturenames:
        return
    problem = phase_discovery_problem()
    if problem:
        metafunc.parametrize("phase", [problem], ids=["phases-missing"], indirect=True)
        return
    phases = discover_phases(_PROJECT_ROOT)
    selected = metafunc.config.getoption("phase")
    if selected is not None and not metafunc.definition.get_closest_marker("project_integrity"):
        phases = [p for p in phases if p["phase_id"] == selected]
        if not phases:
            raise pytest.UsageError(f"Phase not found: {selected!r}")
    metafunc.parametrize(
        "phase",
        phases,
        ids=[p["phase_id"] for p in phases],
        indirect=True,
    )
