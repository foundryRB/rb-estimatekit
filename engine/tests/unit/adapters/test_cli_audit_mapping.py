"""CLI audit presentation exposes adapter fields, including when the domain grows."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.adapters.inbound.cli.commands.registry import COMMANDS
from engine.adapters.inbound.cli.utils import runner
from engine.domain.model.value_objects.audit_report import AuditCheckResult, AuditReport
from engine.domain.model.value_objects.audit_suggestion import AuditSuggestion


@dataclass(frozen=True)
class ExtendedAuditReport(AuditReport):
    """An internal domain field must not leak through generic serialization."""

    internal_context: str = "domain-only"


@pytest.mark.parametrize("phase,passed", [(None, False), ("P2", True)])
def test_command_maps_before_presenting_public_audit_json(
    phase: str | None,
    passed: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The unmapped formatter exposed every domain field through asdict."""
    report = ExtendedAuditReport(
        checks=[AuditCheckResult("check[P2]", "check[P2]", "activity", "passed", "")],
        passed_count=1,
        failed_count=0,
        skipped_count=0,
        passed=passed,
        duration_ms=7,
        suggestions=[AuditSuggestion("risk", "Risk", "Shared context", "scheduling")],
        phase=phase,
    )
    port = SimpleNamespace(execute=lambda project_path, phase: report)
    monkeypatch.setattr(runner, "Container", lambda: SimpleNamespace(run_audit=lambda: port))
    spec = next(command for command in COMMANDS if command.name == "audit")
    result = runner.run(spec, argparse.Namespace(project=Path("example"), phase=phase))
    payload = json.loads(capsys.readouterr().out)
    assert result == (0 if passed else 1)
    assert payload == {
        "checks": [{
            "node_id": "check[P2]", "name": "check[P2]", "category": "activity",
            "outcome": "passed", "message": "",
        }],
        "passed_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "passed": passed,
        "duration_ms": 7,
        "suggestions": [{
            "code": "risk", "title": "Risk", "detail": "Shared context",
            "category": "scheduling", "severity": "warning",
        }],
        "phase": phase,
    }
