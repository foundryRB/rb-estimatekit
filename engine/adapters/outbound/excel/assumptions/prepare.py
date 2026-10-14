"""Extract all assumptions data from domain objects."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from engine.domain.model.aggregates.project import Project

from .models import (
    CONF_ORDER,
    IMPACT_ORDER,
    AssumptionRow,
    AssumptionsData,
    KeyRisk,
    LegendDef,
    LogData,
    RiskMatrixData,
    TraceabilityData,
    TraceRow,
)


def _read_definitions(source_path: Path | None, filename: str) -> list[LegendDef]:
    """Read TSV definitions for legend. Returns empty list on failure."""
    if source_path is None:
        return []
    tsv_path = source_path / "data" / "assumptions" / filename
    if not tsv_path.exists():
        return []
    result: list[LegendDef] = []
    with open(tsv_path, encoding="utf-8", newline="") as f:
        for d in csv.DictReader(f, delimiter="\t"):
            level = d.get("Confidence", d.get("Impact", d.get("Level", "")))
            desc = d.get("Description", d.get("Definition", ""))
            if level:
                result.append(LegendDef(level=level, description=desc))
    return result


def _unique_groups(assumptions: list) -> list[str]:
    """Return unique groups in encounter order."""
    seen: set[str] = set()
    result: list[str] = []
    for a in assumptions:
        if a.group not in seen:
            seen.add(a.group)
            result.append(a.group)
    return result


def prepare_assumptions(project: Project) -> AssumptionsData | None:
    """Extract plain data from domain objects. No openpyxl types."""
    if not project.assumptions:
        return None

    name = project.config.name
    assumptions = project.assumptions

    # ── Log data ────────────────────────────────────────────
    conf_defs = _read_definitions(project.source_path, "00-confidence.tsv")
    impact_defs = _read_definitions(project.source_path, "01-impact.tsv")
    groups = _unique_groups(assumptions)

    grouped_rows: dict[str, list[AssumptionRow]] = {}
    for a in assumptions:
        row = AssumptionRow(
            assumption_id=a.assumption_id,
            group=a.group,
            assumption=a.assumption,
            confidence=a.confidence.value,
            impact=a.impact.value,
            req_ids_str=", ".join(sorted(str(r) for r in a.req_ids)) if a.req_ids else "",
        )
        grouped_rows.setdefault(a.group, []).append(row)

    log = LogData(
        project_name=name,
        conf_defs=conf_defs,
        impact_defs=impact_defs,
        groups=groups,
        grouped_rows=grouped_rows,
    )

    # ── Risk Matrix data ────────────────────────────────────
    matrix: dict[tuple[str, str], int] = defaultdict(int)
    for a in assumptions:
        matrix[(a.confidence.value, a.impact.value)] += 1

    key_risks = [
        KeyRisk(
            assumption_id=a.assumption_id,
            short_title=a.short_title,
            impact=a.impact.value,
        )
        for a in assumptions
        if a.is_high_risk
    ]

    risk = RiskMatrixData(
        project_name=name,
        total=len(assumptions),
        matrix=dict(matrix),
        key_risks=key_risks,
    )

    # ── Traceability data ───────────────────────────────────
    conf_rank = {v: i for i, v in enumerate(CONF_ORDER)}
    impact_rank = {v: i for i, v in enumerate(IMPACT_ORDER)}

    req_map: dict[str, list] = defaultdict(list)
    for a in assumptions:
        for rid in a.req_ids:
            req_map[str(rid)].append(a)

    trace_rows: list[TraceRow] = []
    for req_id, linked in sorted(req_map.items()):
        ids_str = ", ".join(la.assumption_id for la in linked)
        worst_conf = max(
            linked, key=lambda x: conf_rank.get(x.confidence.value, 0),
        ).confidence.value
        worst_imp = max(
            linked, key=lambda x: impact_rank.get(x.impact.value, 0),
        ).impact.value
        trace_rows.append(TraceRow(
            req_id=req_id,
            count=len(linked),
            assumption_ids_str=ids_str,
            worst_confidence=worst_conf,
            worst_impact=worst_imp,
        ))

    traceability = TraceabilityData(project_name=name, rows=trace_rows)

    return AssumptionsData(log=log, risk_matrix=risk, traceability=traceability)
