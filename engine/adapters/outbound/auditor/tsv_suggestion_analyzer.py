"""Outbound adapter: derive advisory delivery-risk suggestions from a project.

Loads a project's phase inputs (config + effort streams) via the persistence
loaders and, when a roadmap has been generated, its milestone layout, then runs
the pure :mod:`delivery_risk_analyzer` rules over them. All file I/O lives here;
the rules stay pure.
"""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.persistence.phase_loaders import (
    load_phase_config,
    load_phases,
    load_project_activities,
    load_resource_rows,
)
from engine.adapters.outbound.persistence.tsv_io import read_tsv
from engine.domain.constants.columns import COL_PROFILE, COL_STREAM, RESOURCE_SKIP_COLS
from engine.domain.constants.files.inputs import DIR_ACTIVITIES, DIR_REQUIREMENTS
from engine.domain.model.value_objects.audit_suggestion import AuditSuggestion
from engine.domain.services.delivery_risk_analyzer import (
    PhaseRiskInput,
    ResourceAllocation,
    analyze_delivery_risks,
)

__all__ = ["TsvSuggestionAnalyzer"]

_MILESTONE_MARK = "◆"
_ROADMAP_BUILD_ALL = Path("output") / "roadmap" / "Roadmap-BuildAll.tsv"


def _allocations(rows: list[dict[str, str]]) -> list[ResourceAllocation]:
    """Turn raw resource rows into per-member monthly allocation series."""
    if not rows:
        return []
    month_cols = [k for k in rows[0] if k not in RESOURCE_SKIP_COLS]
    result: list[ResourceAllocation] = []
    for row in rows:
        label = row.get(COL_PROFILE, "").strip() or row.get(COL_STREAM, "").strip()
        if not label:
            continue
        monthly: list[float] = []
        for col in month_cols:
            raw = row.get(col, "").strip()
            try:
                monthly.append(float(raw) if raw else 0.0)
            except ValueError:
                monthly.append(0.0)
        result.append(ResourceAllocation(label=label, monthly=monthly))
    return result


class TsvSuggestionAnalyzer:
    """Load a project's phase inputs and run the delivery-risk rules over them."""

    def analyze(self, project_path: Path) -> list[AuditSuggestion]:
        data_dir = project_path / "data"
        req_dir = data_dir / DIR_REQUIREMENTS
        act_dir = data_dir / DIR_ACTIVITIES
        inputs: list[PhaseRiskInput] = []
        for phase in load_phases(req_dir):
            phase_id = phase.phase_id
            stream_effort: dict[str, float] = {}
            for act in load_project_activities(act_dir, phase_id):
                stream = act.stream.strip()
                if stream:
                    stream_effort[stream] = stream_effort.get(stream, 0.0) + act.effort_md
            inputs.append(
                PhaseRiskInput(
                    phase_id=phase_id,
                    config=load_phase_config(act_dir, phase_id),
                    stream_effort=stream_effort,
                    allocations=_allocations(load_resource_rows(act_dir, phase_id)),
                )
            )
        return analyze_delivery_risks(
            inputs,
            milestones_by_month=self._milestones_by_month(project_path),
        )

    def _milestones_by_month(self, project_path: Path) -> dict[str, int] | None:
        """Count ◆ build milestones per month from the generated roadmap, if any.

        Returns ``None`` when no roadmap has been generated yet, so the
        milestone-clustering rule simply stays silent until there is output.
        """
        path = project_path / _ROADMAP_BUILD_ALL
        if not path.exists():
            return None
        rows = read_tsv(path)
        if not rows:
            return None
        keys = list(rows[0].keys())
        # Month columns follow the Milestone / Effort (MD) marker column.
        if "Milestone" in keys:
            start = keys.index("Milestone") + 1
        elif "Effort (MD)" in keys:
            start = keys.index("Effort (MD)") + 1
        else:
            start = 1
        month_cols = keys[start:]
        counts: dict[str, int] = {}
        for row in rows:
            for col in month_cols:
                if row.get(col, "").strip() == _MILESTONE_MARK:
                    counts[col] = counts.get(col, 0) + 1
        return counts or None
