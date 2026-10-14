"""Regression tests for the effort slide's arithmetic as a reader checks it.

A signer checks a deck by adding the column up. Two things therefore have to
hold on the page itself, not merely in the values behind it: the phase rows must
sum to the total printed under them, and the agenda must quote the same total
the effort slide does. Rounding each row to a whole day while leaving the total
unrounded broke the first; the agenda truncating where the effort slide rounded
broke the second.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from engine.adapters.outbound.slidev import agenda
from engine.adapters.outbound.slidev.effort import _render_effort_estimate
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.resource_plan import ResourcePlan

# The reported shape: three phases, two carrying a half day. The rows read
# 30 / 30 / 30 and the total read 91.
PHASE_EFFORTS = [("P1", 30.0), ("P2", 30.5), ("P3", 30.5)]


def _project(phase_efforts: list[tuple[str, float]]) -> Project:
    phases = [
        Phase(
            phase_id=pid,
            name=f"Phase {pid}",
            description="",
            build_activities=[
                BuildActivity(activity_id=f"B-{pid}", group="Core", name="Work",
                              effort_md=md),
            ],
            resource_plan=ResourcePlan(streams={"2.Dev": [md]}),
        )
        for pid, md in phase_efforts
    ]
    config = ProjectConfig(
        name="Test Project",
        short_name="Test",
        client="Test Client",
        author="TestCorp",
        description="A test project",
        date="August 2026",
    )
    return Project(config=config, phases=phases)


def _effort_slide(project: Project, tmp_path: Path) -> str:
    efforts = project.compute_all_efforts()
    filename = _render_effort_estimate(project, efforts, tmp_path)
    assert filename == "09-effort-estimate.md"
    return (tmp_path / "pages" / filename).read_text(encoding="utf-8")


def _effort_column(content: str) -> tuple[list[float], float]:
    """The summary table's Effort column: the phase cells, and the TOTAL cell."""
    rows, total = [], None
    for line in content.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not cells[0].startswith("**"):
            continue
        effort = float(cells[4].strip("*"))
        if "TOTAL" in cells[0]:
            total = effort
        else:
            rows.append(effort)
    assert total is not None, f"no TOTAL row parsed from:\n{content}"
    return rows, total


class TestTheTablePrintsArithmeticThatCloses:
    def test_phase_rows_sum_to_the_printed_total(self, tmp_path: Path) -> None:
        rows, total = _effort_column(_effort_slide(_project(PHASE_EFFORTS), tmp_path))
        assert rows == [30.0, 30.5, 30.5]
        assert sum(rows) == pytest.approx(total)
        assert total == pytest.approx(91.0)

    @pytest.mark.parametrize(
        "efforts",
        [
            [("P1", 30.5), ("P2", 30.5), ("P3", 30.5)],
            [("P1", 31.5), ("P2", 31.5), ("P3", 10.0)],
            [("Demo", 0.5), ("P1", 0.5)],
            [("P1", 75.0), ("P2", 251.0)],
        ],
    )
    def test_it_closes_for_any_half_day_shape(
        self, efforts: list[tuple[str, float]], tmp_path: Path
    ) -> None:
        rows, total = _effort_column(_effort_slide(_project(efforts), tmp_path))
        assert sum(rows) == pytest.approx(total)

    def test_a_half_day_reaches_the_page(self, tmp_path: Path) -> None:
        content = _effort_slide(_project(PHASE_EFFORTS), tmp_path)
        assert "30.5" in content


class TestTheDeckAgreesWithItself:
    def test_agenda_quotes_the_effort_slide_total(self, tmp_path: Path) -> None:
        project = _project(PHASE_EFFORTS)
        efforts = project.compute_all_efforts()
        _, slide_total = _effort_column(_effort_slide(project, tmp_path))

        agenda.render(project, project.phases[-1], efforts, [], tmp_path)
        agenda_page = (tmp_path / "pages" / "01-agenda.md").read_text(encoding="utf-8")
        quoted = re.search(r"\*\*Effort Estimate\*\* .*? ([\d.]+) MD", agenda_page)
        assert quoted, f"no effort total found in:\n{agenda_page}"
        assert float(quoted.group(1)) == pytest.approx(slide_total)

    def test_agenda_names_each_phase_at_its_own_precision(self, tmp_path: Path) -> None:
        project = _project(PHASE_EFFORTS)
        agenda.render(project, project.phases[-1], project.compute_all_efforts(), [], tmp_path)
        agenda_page = (tmp_path / "pages" / "01-agenda.md").read_text(encoding="utf-8")
        assert "P1: 30 " in agenda_page
        assert "P2: 30.5" in agenda_page
        assert "P3: 30.5" in agenda_page
