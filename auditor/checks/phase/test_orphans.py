"""No phase-prefixed data file lingers for a phase the project does not define.

A ``P<n>-`` file under any data subdirectory (activities, architecture,
slides) belongs to phase ``P<n>``. A leftover for an undefined phase, typically
a scaffold remnant after re-phasing, would surface in file listings, in the
deck or in the workbooks as content the engagement never authored. The sweep
derives its universe from the data directory, so every kind of phase file is
covered.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from auditor.phases import discover_phases

logger = logging.getLogger(__name__)

_PHASE_PREFIX_RE = re.compile(r"^(P\d+)-")


def test_no_phase_files_for_undefined_phases(project_root: Path) -> None:
    """Every phase-prefixed file under data/ maps to a defined phase."""
    defined = {p["phase_id"] for p in discover_phases(project_root)}
    data_dir = project_root / "data"
    if not data_dir.is_dir():
        return

    orphans: list[str] = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        m = _PHASE_PREFIX_RE.match(path.name)
        if m and m.group(1) not in defined:
            orphans.append(path.relative_to(data_dir).as_posix())

    logger.info("Defined phases: %s; orphans: %s", sorted(defined), orphans)
    assert len(orphans) == 0, (
        f"Files exist for phases not defined in 02-phases.tsv "
        f"(delete them or define the phase): {', '.join(orphans)}"
    )
