"""Subprocess entrypoint: run the auditor against one project in a clean process.

``PytestAuditorRunner`` spawns this module (``python -m …_subprocess_main``) once
per audit so each run gets a fresh interpreter. This matters because the auditor
resolves its project root at conftest *import* time; the engine is a long-lived
process that audits many projects, so an in-process re-run would keep the first
project's root and silently audit the wrong project. A new process per audit is
the isolation boundary.

Contract (all via environment, set by the parent):
  ESTIMATEKIT_PROJECT            the project to audit (the auditor reads this)
  ESTIMATEKIT_AUDIT_PHASE        optional phase id, empty for the whole project
  ESTIMATEKIT_AUDITOR_DIR        the ``auditor/`` suite directory to run
  ESTIMATEKIT_AUDIT_RESULT_PATH  where to write the JSON results array

Exit code is pytest's own (0 all passed, 1 some failed); the parent treats any
other code as a runner failure.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from engine.adapters.outbound.auditor.pytest_auditor_runner import _ResultCollector


def main() -> int:
    auditor_dir = os.environ["ESTIMATEKIT_AUDITOR_DIR"]
    result_path = os.environ["ESTIMATEKIT_AUDIT_RESULT_PATH"]

    collector = _ResultCollector()
    phase = os.environ.get("ESTIMATEKIT_AUDIT_PHASE")
    scope_args = ["--phase", phase] if phase else []
    exit_code = pytest.main(
        [
            auditor_dir,
            *scope_args,
            "-q",
            "--tb=line",
            "--no-header",
            "-p", "no:cacheprovider",
            "-W", "ignore::pytest.PytestAssertRewriteWarning",
        ],
        plugins=[collector],
    )

    payload = [
        {
            "node_id": c.node_id,
            "name": c.name,
            "category": c.category,
            "outcome": c.outcome,
            "message": c.message,
        }
        for c in collector.results
    ]
    Path(result_path).write_text(json.dumps(payload), encoding="utf-8")
    return int(exit_code)


if __name__ == "__main__":
    sys.exit(main())
