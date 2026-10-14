"""Outbound adapter: run the auditor via pytest programmatic API.

This adapter shells into pytest.main() with a lightweight collector plugin
to capture structured results — no extra dependencies required.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from auditor.phases import discover_phases
from engine.domain.exceptions.phase_not_found_error import PhaseNotFoundError
from engine.domain.model.value_objects.audit_report import AuditCheckResult, AuditReport

__all__ = ["PytestAuditorRunner"]

# Pattern to extract category from a nodeid like
# "auditor/checks/brd/test_coverage.py::test_…"
_CATEGORY_RE = re.compile(r"auditor/checks/([^/]+)/")


def _extract_category(node_id: str) -> str:
    m = _CATEGORY_RE.search(node_id.replace("\\", "/"))
    return m.group(1) if m else "unknown"


def _short_name(node_id: str) -> str:
    """Turn ``…/test_foo.py::test_bar[P1]`` into ``test_bar[P1]``."""
    return node_id.rsplit("::", 1)[-1] if "::" in node_id else node_id


class _ResultCollector:
    """Minimal pytest plugin that records per-test outcomes."""

    def __init__(self) -> None:
        self.results: list[AuditCheckResult] = []

    # pytest hook
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:  # noqa: D401
        """Called for each test phase (setup / call / teardown)."""
        # We care about the "call" phase for pass/fail/skip
        # and "setup" phase for skips (e.g. fixture-level skip)
        if report.when == "call":
            if report.skipped:
                # pytest.skip() called inside the test body
                reason = ""
                if report.longrepr and isinstance(report.longrepr, tuple):
                    reason = str(report.longrepr[2])
                elif report.longrepr:
                    reason = str(report.longrepr)
                self.results.append(
                    AuditCheckResult(
                        node_id=report.nodeid,
                        name=_short_name(report.nodeid),
                        category=_extract_category(report.nodeid),
                        outcome="skipped",
                        message=reason,
                    )
                )
            else:
                outcome = "passed" if report.passed else "failed"
                message = ""
                if report.failed:
                    message = str(report.longrepr).strip() if report.longrepr else ""
                    # Truncate very long tracebacks to keep the response lean
                    if len(message) > 500:
                        message = message[:497] + "..."
                self.results.append(
                    AuditCheckResult(
                        node_id=report.nodeid,
                        name=_short_name(report.nodeid),
                        category=_extract_category(report.nodeid),
                        outcome=outcome,
                        message=message,
                    )
                )
        elif report.when == "setup" and report.skipped:
            reason = ""
            if report.longrepr and isinstance(report.longrepr, tuple):
                reason = str(report.longrepr[2])
            elif report.longrepr:
                reason = str(report.longrepr)
            self.results.append(
                AuditCheckResult(
                    node_id=report.nodeid,
                    name=_short_name(report.nodeid),
                    category=_extract_category(report.nodeid),
                    outcome="skipped",
                    message=reason,
                )
            )


class PytestAuditorRunner:
    """Run the ``auditor/`` suite in a fresh subprocess and collect results.

    A subprocess per audit is deliberate. The auditor resolves its project root
    at conftest *import* time, and this engine is a long-lived process that runs
    many audits; an in-process re-run would keep the first project's root and
    silently audit the wrong project. A clean interpreter per run — with
    ``ESTIMATEKIT_PROJECT`` set in its environment — is the isolation boundary.
    """

    def __init__(self, auditor_dir: Path | None = None) -> None:
        self._auditor_dir = auditor_dir or Path(__file__).resolve().parents[4] / "auditor"

    def run(self, project_path: Path, phase: str | None = None) -> AuditReport:
        """Execute all auditor checks against *project_path* in a child process."""
        if phase is not None:
            defined = [p["phase_id"] for p in discover_phases(project_path)]
            if phase not in defined:
                raise PhaseNotFoundError(phase, defined)
        repo_root = self._auditor_dir.parent

        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "audit.json"
            env = os.environ.copy()
            env["ESTIMATEKIT_PROJECT"] = str(project_path.resolve())
            env["ESTIMATEKIT_AUDIT_PHASE"] = phase or ""
            env["ESTIMATEKIT_AUDITOR_DIR"] = str(self._auditor_dir)
            env["ESTIMATEKIT_AUDIT_RESULT_PATH"] = str(result_path)
            # Ensure the child can import the engine package regardless of how the
            # parent was launched (installed or run from the repo).
            env["PYTHONPATH"] = os.pathsep.join(
                p for p in (str(repo_root), env.get("PYTHONPATH", "")) if p
            )

            t0 = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-m",
                 "engine.adapters.outbound.auditor._subprocess_main"],
                cwd=str(repo_root),
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            # pytest exits 0 (all passed) or 1 (some failed); both are valid audit
            # outcomes. Anything else (collection/internal error) is a runner fault.
            if proc.returncode not in (0, 1) or not result_path.exists():
                raise RuntimeError(
                    "auditor subprocess failed "
                    f"(exit {proc.returncode}):\n{proc.stderr[-2000:]}"
                )
            raw = json.loads(result_path.read_text(encoding="utf-8"))

        checks = [
            AuditCheckResult(
                node_id=r["node_id"],
                name=r["name"],
                category=r["category"],
                outcome=r["outcome"],
                message=r["message"],
            )
            for r in raw
        ]
        passed = sum(1 for c in checks if c.outcome == "passed")
        failed = sum(1 for c in checks if c.outcome == "failed")
        skipped = sum(1 for c in checks if c.outcome == "skipped")

        return AuditReport(
            checks=checks,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            passed=failed == 0,
            duration_ms=elapsed_ms,
            phase=phase,
        )
