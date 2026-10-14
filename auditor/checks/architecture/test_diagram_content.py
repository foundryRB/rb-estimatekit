"""Each phase's overview diagram reflects that phase's component inventory."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auditor.helpers import fail_if_file_missing, skip_unless_feature_enabled
from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_components_appear_in_overview_diagram(
    project_root: Path, config: dict[str, Any], phase: dict[str, Any]
) -> None:
    """Every component in P<n>-components.tsv is named in P<n>-overview.puml."""
    skip_unless_feature_enabled(config, "architecture")
    phase_id = phase["phase_id"]
    components_path = get_data_file(
        project_root, "architecture", f"{phase_id}-components.tsv"
    )
    diagram_path = get_data_file(
        project_root, "architecture", f"{phase_id}-overview.puml"
    )
    fail_if_file_missing(diagram_path, f"Overview diagram for phase {phase_id}")

    diagram_text = diagram_path.read_text(encoding="utf-8").lower()
    missing = [
        name
        for row in read_tsv(components_path)
        if (name := row.get("Component", "").strip())
        and name.lower() not in diagram_text
    ]

    logger.info("%s: %d component(s) missing from diagram", phase_id, len(missing))
    assert len(missing) == 0, (
        f"{diagram_path.name} does not mention component(s) from "
        f"{components_path.name}: {', '.join(missing)} — the overview diagram "
        f"must depict the phase's component inventory"
    )
