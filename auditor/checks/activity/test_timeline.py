"""Design and QA timeline feasibility checks."""

from __future__ import annotations

import logging
import math
from typing import Any

from auditor.checks.activity.helpers import (
    DAYS_PER_MONTH,
    month_columns,
    parse_md,
    read_config,
    resource_total_by_stream,
    stream_effort,
)
from auditor.project import get_phase_file
from auditor.tsv import read_tsv
from engine.domain.constants.scheduling import is_qa_stream

logger = logging.getLogger(__name__)


def test_design_timeline_feasibility(phase: dict[str, Any]) -> None:
    """Design capacity in design window covers Design effort."""
    config = read_config(get_phase_file(phase, "config_file"))
    design_lead_days: float = config["design_lead_days"]
    pid = phase["phase_id"]

    if design_lead_days == 0:
        logger.info("%s Design Lead = 0d — concurrent, skipping", pid)
        return

    resource_rows = read_tsv(get_phase_file(phase, "resource_file"))
    project_rows = read_tsv(get_phase_file(phase, "project_file"))
    cols = month_columns(resource_rows)
    n_months = len(cols)
    design_lead_months = math.ceil(design_lead_days / DAYS_PER_MONTH)
    design_end = min(design_lead_months, n_months)
    design_eff = stream_effort(project_rows, "1.Design")

    design_cap = 0.0
    for row in resource_rows:
        if row.get("Stream", "").startswith("1.Design"):
            for col in cols[:design_end]:
                design_cap += parse_md(row.get(col, ""))

    logger.info(
        "%s Design: lead=%.0fd, window=M1-M%d, cap=%g, effort=%g",
        pid, design_lead_days, design_end, design_cap, design_eff,
    )
    assert design_end <= n_months
    assert design_cap >= design_eff, (
        f"{pid}: Design capacity ({design_cap:g}) < effort ({design_eff:g})"
    )


def test_qa_timeline_feasibility(phase: dict[str, Any]) -> None:
    """QA timeline is feasible given Config parameters.

    The QA window reads the test streams (``is_qa_stream``: the scaffold's
    3.Test, or 3.Quality): their capacity from the QA start month on must
    cover their effort.
    """
    config = read_config(get_phase_file(phase, "config_file"))
    design_lead_days: float = config["design_lead_days"]
    lag_pct: float = config["lag_pct"]
    sit_days: float = config["sit_days"]
    uat_days: float = config["uat_days"]
    pid = phase["phase_id"]

    if sit_days == 0 and uat_days == 0 and lag_pct == 0:
        logger.info("%s No formal testing configured — skipping", pid)
        return

    resource_rows = read_tsv(get_phase_file(phase, "resource_file"))
    project_rows = read_tsv(get_phase_file(phase, "project_file"))
    cols = month_columns(resource_rows)
    n_months = len(cols)

    dev_eff = stream_effort(project_rows, "2.Dev")
    test_eff = sum(
        parse_md(row.get("Effort (MD)", ""))
        for row in project_rows
        if is_qa_stream(row.get("Stream", ""))
    )
    design_lead_months = (
        math.ceil(design_lead_days / DAYS_PER_MONTH) if design_lead_days > 0 else 0
    )
    test_months = (
        math.ceil((sit_days + uat_days) / DAYS_PER_MONTH)
        if (sit_days + uat_days) > 0
        else 0
    )
    build_start = design_lead_months
    build_end = max(build_start + 1, n_months - test_months)
    build_span = build_end - build_start

    dev_total_cap = resource_total_by_stream(resource_rows, "2.Dev")
    qa_start = build_start + (
        math.ceil(lag_pct / 100.0 * build_span) if lag_pct > 0 else 0
    )

    qa_cap = 0.0
    for row in resource_rows:
        if is_qa_stream(row.get("Stream", "")):
            for col in cols[qa_start:]:
                qa_cap += parse_md(row.get(col, ""))

    dev_in_test = 0.0
    for row in resource_rows:
        if row.get("Stream", "").startswith("2.Dev"):
            for col in cols[build_end:]:
                dev_in_test += parse_md(row.get(col, ""))

    logger.info("%s QA: lag=%.0f%%, SIT=%.0fd, UAT=%.0fd", pid, lag_pct, sit_days, uat_days)
    logger.info(
        "  Timeline: %dmo = %d design + %d build + %d test",
        n_months, design_lead_months, build_end - build_start, test_months,
    )
    logger.info("  2.Dev: cap=%g, effort=%g", dev_total_cap, dev_eff)
    logger.info("  QA streams: cap=%g (from M%d), effort=%g", qa_cap, qa_start + 1, test_eff)

    assert dev_total_cap >= dev_eff, (
        f"{pid}: 2.Dev capacity ({dev_total_cap:g}) < effort ({dev_eff:g})"
    )
    assert qa_cap >= test_eff, (
        f"{pid}: QA capacity from M{qa_start + 1} ({qa_cap:g}) < QA effort ({test_eff:g})"
    )
    if test_months > 0:
        assert dev_in_test > 0, f"{pid}: No dev during SIT/UAT"
