"""No scaffold example content remains anywhere in the project data.

The scaffold marks every example value with an explicit sentinel
(``[EXAMPLE]``, ``[PROJECT NAME]``, ``[Client Name]``). A project is not
delivery-ready while any sentinel survives: whatever still carries one was
never authored for the engagement and would ship as example content.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SENTINELS = ("[EXAMPLE]", "[PROJECT NAME]", "[Client Name]")

_MAX_LISTED = 8


def _iter_candidate_files(project_root: Path) -> list[Path]:
    """``project.yaml`` plus every file under ``data/``, deterministic order."""
    files = [project_root / "project.yaml"]
    data_dir = project_root / "data"
    if data_dir.is_dir():
        files.extend(sorted(p for p in data_dir.rglob("*") if p.is_file()))
    return files


def _sentinel_hits(path: Path, project_root: Path) -> list[str]:
    """Return ``file:line [sentinel]`` entries for every sentinel in *path*."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    rel = path.relative_to(project_root).as_posix()
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for sentinel in SENTINELS:
            if sentinel in line:
                hits.append(f"{rel}:{lineno} contains {sentinel}")
    return hits


def test_no_scaffold_sentinels_remain(project_root: Path) -> None:
    """No file still contains scaffold sentinel content."""
    hits: list[str] = []
    for path in _iter_candidate_files(project_root):
        hits.extend(_sentinel_hits(path, project_root))

    logger.info("Scaffold sentinel hits: %d", len(hits))
    listed = "\n".join(hits[:_MAX_LISTED])
    if len(hits) > _MAX_LISTED:
        listed += f"\n... and {len(hits) - _MAX_LISTED} more"
    assert len(hits) == 0, (
        f"{len(hits)} scaffold sentinel(s) remain — replace the example "
        f"content with the engagement's, or delete the file:\n{listed}"
    )
