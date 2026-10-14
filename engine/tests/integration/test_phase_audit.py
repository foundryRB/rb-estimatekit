"""Scoped audits preserve historical phases and shared integrity checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import engine.adapters.inbound.http.dependencies as deps
from engine.adapters.inbound.http.app import create_app
from engine.container import Container
from engine.domain.exceptions.phase_not_found_error import PhaseNotFoundError


def _rewrite(path: Path, key: str, values: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        cells = line.split("\t")
        if cells[0] == key:
            lines[i] = "\t".join([key, *values, *cells[len(values) + 1 :]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def follow_on(tmp_path: Path) -> Path:
    project = Container().scaffold_project().execute(tmp_path, "follow-on")
    for path in [project / "project.yaml", *sorted((project / "data").rglob("*"))]:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for sentinel in ("[EXAMPLE]", "[PROJECT NAME]", "[Client Name]"):
                text = text.replace(sentinel, "Authored")
            path.write_text(text, encoding="utf-8")
    # The frozen phase books QA before the current QA window, leaving zero capacity.
    config = project / "data/activities/P1-config.tsv"
    _rewrite(config, "Testing Lag", ["50"])
    resource = project / "data/activities/P1-resource.tsv"
    _rewrite(resource, "3.Test", ["QA Engineer", "€ 250", "20", "0", "0", "0"])
    return project


def test_scoped_audit_runs_selected_phase_and_global_integrity(follow_on: Path) -> None:
    port = Container().run_audit()
    whole = port.execute(follow_on)
    selected = port.execute(follow_on, phase="P2")
    assert whole.phase is None and not whole.passed
    assert any(
        c.name == "test_qa_timeline_feasibility[P1]" and c.outcome == "failed" for c in whole.checks
    )
    assert selected.phase == "P2" and selected.passed, [
        c for c in selected.checks if c.outcome == "failed"
    ]
    assert "test_qa_timeline_feasibility[P1]" not in {c.name for c in selected.checks}
    assert "test_qa_timeline_feasibility[P2]" in {c.name for c in selected.checks}
    assert "test_all_phases_summary" in {c.name for c in selected.checks}
    assert not port.execute(follow_on, phase="P1").passed
    with pytest.raises(PhaseNotFoundError, match="P99"):
        port.execute(follow_on, phase="P99")


@pytest.mark.parametrize("corruption", ["duplicate-id", "undefined-phase", "historical-reference"])
def test_shared_corruption_fails_selected_audit(follow_on: Path, corruption: str) -> None:
    if corruption == "duplicate-id":
        path = follow_on / "data/requirements/01-brd.tsv"
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join([*lines, lines[1]]) + "\n", encoding="utf-8")
    elif corruption == "undefined-phase":
        path = follow_on / "data/requirements/03-matrix.tsv"
        text = path.read_text(encoding="utf-8").replace("Phase 1", "Undefined Phase", 1)
        path.write_text(text, encoding="utf-8")
    else:
        path = follow_on / "data/activities/P1-build.tsv"
        lines = path.read_text(encoding="utf-8").splitlines()
        cells = lines[1].split("\t")
        cells[lines[0].split("\t").index("Req IDs")] = "MISSING-999"
        lines[1] = "\t".join(cells)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = Container().run_audit().execute(follow_on, phase="P2")
    assert not report.passed
    expected = {
        "duplicate-id": "test_no_duplicate_brd_requirements",
        "undefined-phase": "test_phase_definitions_match",
        "historical-reference": "test_activities_reference_valid_requirements[P1]",
    }[corruption]
    assert any(c.name == expected and c.outcome == "failed" for c in report.checks)


def test_http_and_cli_expose_scope_and_reject_unknown_phase(
    follow_on: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ESTIMATEKIT_PROJECTS_ROOT", str(follow_on.parent))
    deps.get_container.cache_clear()
    try:
        with TestClient(create_app()) as client:
            scoped = client.post("/api/projects/follow-on/audit", params={"phase": "P2"})
            assert scoped.status_code == 200 and scoped.json()["phase"] == "P2"
            assert scoped.json()["passed"] is True
            assert (
                client.post("/api/projects/follow-on/audit", params={"phase": "P99"}).status_code
                == 422
            )
    finally:
        deps.get_container.cache_clear()
    cli = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine.adapters.inbound.cli",
            "audit",
            str(follow_on),
            "--phase",
            "P2",
        ],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout)["phase"] == "P2"
    whole_cli = subprocess.run(
        [sys.executable, "-m", "engine.adapters.inbound.cli", "audit", str(follow_on)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert whole_cli.returncode == 1 and json.loads(whole_cli.stdout)["phase"] is None
    unknown = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine.adapters.inbound.cli",
            "audit",
            str(follow_on),
            "--phase",
            "P99",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert unknown.returncode == 3 and "Phase not found" in unknown.stderr


def test_unknown_phase_is_refused_when_collecting_only_shared_checks(
    follow_on: Path,
) -> None:
    env = os.environ.copy()
    env["ESTIMATEKIT_PROJECT"] = str(follow_on)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "auditor/checks/brd", "--phase", "P99", "-q"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 4 and "Phase not found" in result.stderr
