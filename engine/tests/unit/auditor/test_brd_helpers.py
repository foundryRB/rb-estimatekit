"""Tests for the auditor's customer-requirements reader (the BRD coverage rule).

The rule: every non-blank line of ``00-customer-requirements.txt`` is cited by at
least one BRD row's Lines. Blank and whitespace-only lines are the only lines
left out; nothing depends on formatting or language.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from auditor.checks.brd.helpers import read_brd_lines, read_customer_requirements

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REQUIREMENT_DIRS = sorted(
    p.parent
    for p in (_REPO_ROOT / "projects").glob("*/data/requirements/00-customer-requirements.txt")
) + [_REPO_ROOT / "templates" / "requirements"]


def _label(req_dir: Path) -> str:
    """The test id of a requirements folder: its project's slug, or ``template``."""
    return "template" if req_dir.parent.name == "templates" else req_dir.parents[1].name


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "00-customer-requirements.txt"
    path.write_text(text, encoding="utf-8")
    return path


class TestTrackedLines:
    """A line is tracked exactly when it holds anything but whitespace."""

    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            ("- Users sign in with SSO", "- Users sign in with SSO"),
            ("    - Nested bullet", "- Nested bullet"),
            ("Authentication:", "Authentication:"),
            ("States: active, suspended.", "States: active, suspended."),
            ("1. Numbered item", "1. Numbered item"),
            ("Olá equipa,", "Olá equipa,"),
            ("\tBest regards,   ", "Best regards,"),
        ],
    )
    def test_non_blank_lines_are_tracked_stripped(
        self, tmp_path: Path, line: str, expected: str
    ) -> None:
        assert read_customer_requirements(_write(tmp_path, line + "\n")) == {1: expected}

    @pytest.mark.parametrize("line", ["", "   ", "\t", " \t "])
    def test_blank_lines_are_not_tracked(self, tmp_path: Path, line: str) -> None:
        assert read_customer_requirements(_write(tmp_path, line + "\n")) == {}

    def test_a_byte_order_mark_is_not_content(self, tmp_path: Path) -> None:
        text = "\ufeff\n- Users sign in with SSO\n"
        assert read_customer_requirements(_write(tmp_path, text)) == {2: "- Users sign in with SSO"}

    def test_line_numbers_are_one_indexed(self, tmp_path: Path) -> None:
        text = "Hello team,\n\nAuthentication:\n- Users sign in with SSO\n\n  \nBest regards,\n"
        assert read_customer_requirements(_write(tmp_path, text)) == {
            1: "Hello team,",
            3: "Authentication:",
            4: "- Users sign in with SSO",
            7: "Best regards,",
        }


class TestBundledRequirements:
    """Every bundled project, and the scaffold template, cites every non-blank line."""

    @pytest.mark.parametrize(
        "req_dir",
        _REQUIREMENT_DIRS,
        ids=[_label(p) for p in _REQUIREMENT_DIRS],
    )
    def test_every_non_blank_line_is_cited(self, req_dir: Path) -> None:
        tracked = read_customer_requirements(req_dir / "00-customer-requirements.txt")
        covered, _ = read_brd_lines(req_dir / "01-brd.tsv")
        assert tracked, "the requirements file is empty"
        assert sorted(set(tracked) - covered) == []
