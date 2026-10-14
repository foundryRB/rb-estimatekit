"""Loaders: per-phase data from TSV files."""

from __future__ import annotations

from pathlib import Path

from engine.adapters.outbound.persistence.requirement_loaders import parse_req_ids_raw
from engine.adapters.outbound.persistence.tsv_io import read_tsv
from engine.domain.constants.columns import (
    COL_ACTIVITY,
    COL_ACTIVITY_GROUP,
    COL_ACTIVITY_ID,
    COL_COMPONENT,
    COL_DESCRIPTION,
    COL_EFFORT_MD,
    COL_EXAMPLES,
    COL_GROUP,
    COL_INTEGRATION_TYPE,
    COL_KEY,
    COL_LAYER,
    COL_NAME,
    COL_PARAMETER,
    COL_PHASE,
    COL_PHASE_ID,
    COL_POSITION,
    COL_REQ_IDS,
    COL_SECTION,
    COL_SLIDE,
    COL_STREAM,
    COL_TECHNOLOGY,
    COL_TEXT,
    COL_VALUE,
    CONFIG_PARAM_MAP,
    RESOURCE_SKIP_COLS,
)
from engine.domain.constants.files.inputs import (
    FILE_PHASES,
    SLIDES_EXECUTIVE_SUMMARY,
    SLIDES_NOTES,
    architecture_file,
    phase_file,
    slides_file,
)
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.entities.component import Component
from engine.domain.model.entities.executive_summary_data import ExecutiveSummaryData
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.entities.slide_note import SlideNote
from engine.domain.model.value_objects.phase_config import PhaseConfig
from engine.domain.model.value_objects.requirement_id import RequirementId
from engine.domain.model.value_objects.resource_plan import ResourcePlan

__all__ = [
    "load_build_activities",
    "load_components",
    "load_executive_summary",
    "load_phase_config",
    "load_phases",
    "load_project_activities",
    "load_resource_plan",
    "load_resource_rows",
    "load_slide_notes",
]


def load_phases(data_dir: Path) -> list[Phase]:
    """Load requirements/02-phases.tsv → list[Phase]."""
    path = data_dir / FILE_PHASES
    if not path.exists():
        return []
    rows = read_tsv(path)
    return [
        Phase(
            phase_id=row.get(COL_PHASE_ID, ""),
            phase_name=row.get(COL_PHASE, ""),
            name=row.get(COL_NAME, ""),
            description=row.get(COL_DESCRIPTION, ""),
            integration_type=row.get(COL_INTEGRATION_TYPE, ""),
            examples=row.get(COL_EXAMPLES, ""),
        )
        for row in rows
        if row.get(COL_PHASE_ID, "").strip()
    ]


def load_build_activities(data_dir: Path, phase_id: str) -> list[BuildActivity]:
    """Load activities/{phase_id}-build.tsv."""
    path = data_dir / phase_file(phase_id, "build")
    if not path.exists():
        return []
    rows = read_tsv(path)
    return [
        BuildActivity(
            activity_id=row.get(COL_ACTIVITY_ID, ""),
            group=row.get(COL_GROUP, ""),
            name=row.get(COL_ACTIVITY, row.get(COL_NAME, "")),
            effort_md=float(row.get(COL_EFFORT_MD, 0) or 0),
            req_ids={RequirementId(r) for r in parse_req_ids_raw(row.get(COL_REQ_IDS, ""))},
        )
        for row in rows
    ]


def load_project_activities(data_dir: Path, phase_id: str) -> list[ProjectActivity]:
    """Load activities/{phase_id}-project.tsv."""
    path = data_dir / phase_file(phase_id, "project")
    if not path.exists():
        return []
    rows = read_tsv(path)
    return [
        ProjectActivity(
            group=row.get(COL_ACTIVITY_GROUP, row.get(COL_GROUP, "")),
            stream=row.get(COL_STREAM, ""),
            effort_md=float(row.get(COL_EFFORT_MD, 0) or 0),
        )
        for row in rows
    ]


def load_resource_plan(data_dir: Path, phase_id: str) -> ResourcePlan:
    """Load activities/{phase_id}-resource.tsv → ResourcePlan.

    Stream columns are everything except Stream, Profile, Rate Day.
    """
    path = data_dir / phase_file(phase_id, "resource")
    if not path.exists():
        return ResourcePlan()
    rows = read_tsv(path)
    if not rows:
        return ResourcePlan()

    # Discover month columns from header (everything not in RESOURCE_SKIP_COLS)
    month_cols = [k for k in rows[0] if k not in RESOURCE_SKIP_COLS]

    streams: dict[str, list[float]] = {}
    for row in rows:
        stream = row.get(COL_STREAM, "").strip()
        if not stream:
            continue
        if stream not in streams:
            streams[stream] = [0.0] * len(month_cols)
        for i, col in enumerate(month_cols):
            val = row.get(col, "0").strip()
            streams[stream][i] += float(val) if val else 0.0

    return ResourcePlan(streams=streams)


def load_resource_rows(data_dir: Path, phase_id: str) -> list[dict[str, str]]:
    """Load activities/{phase_id}-resource.tsv → raw row dicts for quoter."""
    path = data_dir / phase_file(phase_id, "resource")
    if not path.exists():
        return []
    return read_tsv(path)


def load_phase_config(data_dir: Path, phase_id: str) -> PhaseConfig:
    """Load activities/{phase_id}-config.tsv → PhaseConfig.

    Config is Parameter/Value format with days as units.
    """
    path = data_dir / phase_file(phase_id, "config")
    if not path.exists():
        return PhaseConfig()
    rows = read_tsv(path)

    params: dict[str, float] = {}
    for row in rows:
        param = row.get(COL_PARAMETER, "").strip()
        value = row.get(COL_VALUE, "0").strip()
        key = CONFIG_PARAM_MAP.get(param)
        if key:
            params[key] = float(value) if value else 0.0

    return PhaseConfig(
        design_lead_days=params.get("design_lead_days", 0.0),
        lag_pct=params.get("lag_pct", 0.0),
        sit_days=params.get("sit_days", 0.0),
        uat_days=params.get("uat_days", 0.0),
    )


def load_components(data_dir: Path, phase_id: str) -> list[Component]:
    """Load architecture/{phase_id}-components.tsv."""
    path = data_dir / architecture_file(phase_id, "components")
    if not path.exists():
        return []
    rows = read_tsv(path)
    return [
        Component(
            name=row.get(COL_NAME, row.get(COL_COMPONENT, "")),
            layer=row.get(COL_LAYER, ""),
            technology=row.get(COL_TECHNOLOGY, ""),
            description=row.get(COL_DESCRIPTION, ""),
        )
        for row in rows
    ]


def load_slide_notes(data_dir: Path, phase_id: str) -> list[SlideNote]:
    """Load slides/{phase_id}-notes.tsv → list[SlideNote]."""
    path = data_dir / slides_file(phase_id, SLIDES_NOTES)
    if not path.exists():
        return []
    rows = read_tsv(path)
    return [
        SlideNote(
            slide=row.get(COL_SLIDE, ""),
            position=row.get(COL_POSITION, ""),
            text=row.get(COL_TEXT, ""),
        )
        for row in rows
    ]


def load_executive_summary(data_dir: Path, phase_id: str) -> ExecutiveSummaryData | None:
    """Load slides/{phase_id}-executive-summary.tsv → ExecutiveSummaryData."""
    path = data_dir / slides_file(phase_id, SLIDES_EXECUTIVE_SUMMARY)
    if not path.exists():
        return None
    rows = read_tsv(path)
    data = ExecutiveSummaryData()
    for row in rows:
        section = row.get(COL_SECTION, "")
        key = row.get(COL_KEY, "")
        value = row.get(COL_VALUE, "")
        if section == "Context" and key == "Description":
            data.context_description = value
        elif section == "Context" and key == "Bullet":
            data.context_bullets.append(value)
        elif section == "Rationale":
            data.rationale.append((key, value))
        elif section == "Highlight":
            data.highlights.append((key, value))
    return data
