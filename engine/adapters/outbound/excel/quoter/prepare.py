"""Extract quoter data from domain entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.domain.constants.columns import COL_RATE_DAY
from engine.domain.services.rate_parser import parse_rate_day

from .models import QuoterPhaseData, QuoterResourceRow
from .parsing import discover_month_keys

if TYPE_CHECKING:
    from engine.domain.model.aggregates.phase import Phase
    from engine.domain.model.aggregates.project import Project


def prepare_quoter(project: Project, phase: Phase) -> QuoterPhaseData | None:
    """Extract quoter data from domain entities. No openpyxl imports."""
    resources = phase.resource_rows
    if not resources:
        return None

    month_keys = discover_month_keys(resources)

    plan: list[tuple[str, QuoterResourceRow | None]] = []
    current_stream: str | None = None
    for res in resources:
        stream = res.get("Stream", "")
        if current_stream is not None and stream != current_stream:
            plan.append(("sep", None))
        current_stream = stream

        profile = res.get("Profile", "")
        rate = parse_rate_day(
            res.get(COL_RATE_DAY, ""),
            context=f"phase {phase.phase_id}, stream {stream!r}, profile {profile!r}",
        )
        days = [float(res.get(m, "0") or "0") for m in month_keys]
        plan.append(("data", QuoterResourceRow(
            stream=stream,
            profile=profile,
            rate=rate,
            days=days,
        )))

    return QuoterPhaseData(
        phase_name=phase.name,
        phase_id=phase.phase_id,
        project_name=project.config.name,
        month_count=len(month_keys),
        plan=plan,
    )
