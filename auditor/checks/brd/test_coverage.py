"""Every non-blank line of the customer requirements is cited by a BRD row."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auditor.checks.brd.helpers import read_brd_lines, read_customer_requirements
from auditor.helpers import fail_if_file_missing, skip_unless_feature_enabled
from auditor.project import get_data_file

logger = logging.getLogger(__name__)


def test_brd_coverage(project_root: Path, config: dict[str, Any]) -> None:
    """Every non-blank line of the customer requirements is cited by a BRD row."""
    skip_unless_feature_enabled(config, "customer_requirements")

    email_path = get_data_file(project_root, "requirements", "00-customer-requirements.txt")
    brd_path = get_data_file(project_root, "requirements", "01-brd.tsv")
    fail_if_file_missing(email_path, "Customer requirements file")
    assert brd_path.exists()

    content_lines = read_customer_requirements(email_path)
    covered, _requirements = read_brd_lines(brd_path)

    uncovered = [(ln, txt) for ln, txt in content_lines.items() if ln not in covered]
    pct = (
        (len(content_lines) - len(uncovered)) / len(content_lines) * 100
        if content_lines
        else 0
    )
    logger.info(
        "BRD coverage: %.1f%% (%d/%d lines)",
        pct,
        len(content_lines) - len(uncovered),
        len(content_lines),
    )

    if uncovered:
        for ln, txt in sorted(uncovered):
            logger.debug("  Line %d: %s", ln, txt[:80])

    assert len(uncovered) == 0, (
        f"BRD does not cover {len(uncovered)} lines:\n"
        + "\n".join(f"  Line {ln}: {txt[:60]}" for ln, txt in sorted(uncovered)[:10])
        + "\n  (Lines in 01-brd.tsv is the 1-indexed line number of the requirement's source"
        " sentence in 00-customer-requirements.txt, plus any heading, lead-in or context lines"
        " the row carries: one number, a comma-separated list, or a start-end range. A pointer,"
        " never a span length.)"
    )
