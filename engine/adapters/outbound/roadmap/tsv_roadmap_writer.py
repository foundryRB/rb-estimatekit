"""TSV roadmap writer — implements RoadmapWriter port.

Thin orchestrator that delegates to focused modules within
the roadmap package:
  view_writers  — per-phase TSV generation
  view_mergers  — cross-phase merged TSV generation
  helpers       — shared utility functions
"""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.roadmap.view_mergers import (
    merge_activity_groups,
    merge_build,
    merge_lifecycle,
    merge_resource,
)
from engine.adapters.outbound.roadmap.view_writers import (
    write_activity_groups,
    write_build,
    write_lifecycle,
    write_resource,
)
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap


class TsvRoadmapWriter:
    """Write roadmap views as TSV files — same format as the original engine."""

    def write_phase(self, output_dir: Path, roadmap: PhaseRoadmap) -> None:
        """Write all four views for a single phase."""
        output_dir.mkdir(parents=True, exist_ok=True)
        pid = roadmap.phase_id
        labels = roadmap.month_labels

        write_resource(output_dir, pid, roadmap.stream_capacities, labels)
        write_activity_groups(output_dir, pid, roadmap.groups_raw, labels)
        write_build(output_dir, pid, roadmap)
        write_lifecycle(output_dir, pid, roadmap)

    def write_merged(self, output_dir: Path, roadmaps: list[PhaseRoadmap]) -> None:
        """Write the merged all-phases view."""
        output_dir.mkdir(parents=True, exist_ok=True)

        merge_resource(output_dir, roadmaps)
        merge_activity_groups(output_dir, roadmaps)
        merge_build(output_dir, roadmaps)
        merge_lifecycle(output_dir, roadmaps)
