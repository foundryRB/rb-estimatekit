"""Every defined phase has its architecture files (feature-gated)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auditor.helpers import fail_if_file_missing, skip_unless_feature_enabled
from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_phase_overview_diagram_exists(
    project_root: Path, config: dict[str, Any], phase: dict[str, Any]
) -> None:
    """Each defined phase has an overview diagram in data/architecture/."""
    skip_unless_feature_enabled(config, "architecture")
    phase_id = phase["phase_id"]
    path = get_data_file(project_root, "architecture", f"{phase_id}-overview.puml")
    fail_if_file_missing(path, f"Overview diagram for phase {phase_id}")


def test_phase_components_defined(
    project_root: Path, config: dict[str, Any], phase: dict[str, Any]
) -> None:
    """Each defined phase has a non-empty component inventory."""
    skip_unless_feature_enabled(config, "architecture")
    phase_id = phase["phase_id"]
    path = get_data_file(project_root, "architecture", f"{phase_id}-components.tsv")
    fail_if_file_missing(path, f"Component inventory for phase {phase_id}")

    rows = [r for r in read_tsv(path) if r.get("Component", "").strip()]
    logger.info("%s: %d component(s)", phase_id, len(rows))
    assert len(rows) > 0, (
        f"{path.name} defines no components for phase {phase_id}"
    )
