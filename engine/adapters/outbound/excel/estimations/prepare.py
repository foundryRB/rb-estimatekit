"""Extract estimation data from domain entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import BuildActivityRow, BuildGroupData, EstimateRow, EstimationData

if TYPE_CHECKING:
    from engine.domain.model.aggregates.phase import Phase
    from engine.domain.model.value_objects.phase_effort import PhaseEffort


def prepare_estimation(phase: Phase, effort: PhaseEffort) -> EstimationData:
    """Extract estimation data from domain entities. No openpyxl imports."""
    groups_dict: dict[str, list[BuildActivityRow]] = {}
    for act in phase.build_activities:
        row = BuildActivityRow(
            name=act.name,
            req_ids_str=", ".join(sorted(str(r) for r in act.req_ids)) if act.req_ids else "",
            effort_md=act.effort_md,
            group=act.group,
        )
        groups_dict.setdefault(act.group, []).append(row)

    build_groups = [
        BuildGroupData(
            group_name=gname,
            activities=acts,
            subtotal=sum(a.effort_md for a in acts),
        )
        for gname, acts in groups_dict.items()
    ]

    estimate_rows = [
        EstimateRow("Build Activities", effort.build_total, is_header=True),
    ]
    for label, md in effort.overhead_rows:
        estimate_rows.append(EstimateRow(label, md))

    return EstimationData(
        phase_name=phase.name,
        phase_id=phase.phase_id,
        build_groups=build_groups,
        build_total=effort.build_total,
        estimate_rows=estimate_rows,
        authored_total=effort.authored_total,
        staffed_capacity=effort.staffed_capacity,
    )
