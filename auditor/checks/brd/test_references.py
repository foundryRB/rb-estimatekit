"""All BRD line references point to actual lines in customer requirements."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auditor.checks.brd.helpers import read_brd_lines
from auditor.helpers import fail_if_file_missing, skip_unless_feature_enabled
from auditor.project import get_data_file

logger = logging.getLogger(__name__)


def test_brd_line_references_valid(project_root: Path, config: dict[str, Any]) -> None:
    """All BRD line references point to actual lines in customer requirements."""
    skip_unless_feature_enabled(config, "customer_requirements")

    email_path = get_data_file(project_root, "requirements", "00-customer-requirements.txt")
    brd_path = get_data_file(project_root, "requirements", "01-brd.tsv")
    fail_if_file_missing(email_path, "Customer requirements file")

    with open(email_path, encoding="utf-8") as f:
        total_lines = len(f.readlines())

    covered, _ = read_brd_lines(brd_path)
    invalid = [ln for ln in covered if ln < 1 or ln > total_lines]
    assert len(invalid) == 0, (
        f"Invalid line refs: {invalid} (file has {total_lines} lines)"
    )
    logger.info("All %d line references valid (1-%d)", len(covered), total_lines)
