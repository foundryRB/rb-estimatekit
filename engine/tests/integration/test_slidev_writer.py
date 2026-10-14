"""Integration tests for SlidevWriter.

Verifies the Slidev presentation writer produces a complete deck from
in-memory domain objects, writing to a temporary directory, and that the deck
sells one phase: its pitch, architecture and sections are that phase's own.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_intent import intent

from engine.adapters.outbound.slidev.slidev_writer import SlidevWriter
from engine.adapters.outbound.slidev.vrom_revenue import compute_phase_revenue
from engine.domain.exceptions import InvalidRateError, PhaseInputMissingError
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.entities.component import Component
from engine.domain.model.entities.executive_summary_data import ExecutiveSummaryData
from engine.domain.model.entities.guideline import Guideline
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.entities.slide_note import SlideNote
from engine.domain.model.value_objects.requirement_id import RequirementId
from engine.domain.model.value_objects.resource_plan import ResourcePlan
from engine.domain.services.roadmap_merger import merge_roadmaps

_P1_EFFORT_NOTE = "The P1 estimate assumes a stable team."
_P2_EFFORT_NOTE = "The P2 estimate assumes the P1 team continues."


def _make_schedulable(phase: Phase) -> None:
    """Give *phase* convention-named streams and BRD mappings so it schedules."""
    phase.resource_plan = ResourcePlan(
        streams={
            "2.Dev Backend": [2.0, 2.0, 2.0, 1.0],
            "3.PM": [0.5, 0.5, 0.5, 0.5],
            "1.Arch": [1.0, 0.5, 0.0, 0.0],
        }
    )
    phase.project_activities = [
        ProjectActivity(group="Build Activities", stream="2.Dev Backend", effort_md=15.0),
        ProjectActivity(group="Design Lead", stream="1.Arch", effort_md=10.0),
    ]
    phase.brd_order = ["Authentication", "Integration"]
    phase.req_to_category = {
        "REQ-001": "Authentication",
        "REQ-002": "Authentication",
        "REQ-003": "Integration",
    }


def _pitch(phase_id: str) -> ExecutiveSummaryData:
    return ExecutiveSummaryData(
        context_description=f"{phase_id} sells its own scope",
        context_bullets=[f"{phase_id} bullet"],
        rationale=[("Platform", f"{phase_id} platform")],
        highlights=[("Delivery", f"{phase_id} delivery")],
    )


def _write(project: Project, phase: Phase, out: Path) -> int:
    efforts = project.compute_all_efforts()
    roadmaps = project.schedule_all_roadmaps()
    if len(roadmaps) >= 2:
        roadmaps = roadmaps + [merge_roadmaps(roadmaps)]
    return SlidevWriter().write_deck(project, phase, efforts, roadmaps, out)


class TestSlidevWriter:
    """End-to-end tests for SlidevWriter using minimal fixtures."""

    @pytest.fixture()
    def schedulable_project(self, minimal_project: Project) -> Project:
        """Patch minimal_project's phase so it schedules and carries its pitch."""
        for phase in minimal_project.phases:
            _make_schedulable(phase)
            phase.executive_summary = _pitch(phase.phase_id)
        return minimal_project

    @pytest.fixture()
    def deck_output(
        self, schedulable_project: Project, tmp_path: Path,
    ) -> tuple[int, Path]:
        """Generate a full slide deck and return (page_count, output_dir)."""
        count = _write(schedulable_project, schedulable_project.phases[0], tmp_path)
        return count, tmp_path

    def test_slides_md_exists(self, deck_output: tuple[int, Path]) -> None:
        """The main slides.md entry point must be generated."""
        _, out = deck_output
        assert (out / "slides.md").exists()

    def test_style_css_exists(self, deck_output: tuple[int, Path]) -> None:
        """The style.css file must be generated."""
        _, out = deck_output
        assert (out / "style.css").exists()

    def test_no_package_json_generated(self, deck_output: tuple[int, Path]) -> None:
        """No per-project package.json — the shared toolchain provides it."""
        _, out = deck_output
        assert not (out / "package.json").exists()

    def test_pages_directory_has_md_files(self, deck_output: tuple[int, Path]) -> None:
        """The pages/ directory must contain at least one .md slide file."""
        _, out = deck_output
        pages = list((out / "pages").glob("*.md"))
        assert len(pages) > 0

    def test_page_count_positive(self, deck_output: tuple[int, Path]) -> None:
        """The writer must return a positive page count."""
        count, _ = deck_output
        assert count > 0

    def test_page_count_matches_files(self, deck_output: tuple[int, Path]) -> None:
        """The returned count must match the number of .md files in pages/."""
        count, out = deck_output
        pages = list((out / "pages").glob("*.md"))
        assert count == len(pages)

    def test_slides_md_references_pages(self, deck_output: tuple[int, Path]) -> None:
        """slides.md must contain src references to page files."""
        _, out = deck_output
        content = (out / "slides.md").read_text(encoding="utf-8")
        assert "src:" in content or "pages/" in content

    def test_slides_md_has_theme_and_color_schema(self, deck_output: tuple[int, Path]) -> None:
        """slides.md frontmatter must set light theme to avoid dark mode."""
        _, out = deck_output
        content = (out / "slides.md").read_text(encoding="utf-8")
        assert "theme: default" in content
        assert "colorSchema: light" in content

    def test_slides_md_src_blocks_are_closed(self, deck_output: tuple[int, Path]) -> None:
        """Each src: import block must be closed with --- to avoid raw text."""
        _, out = deck_output
        content = (out / "slides.md").read_text(encoding="utf-8")
        # Every "src: ./pages/" line must be followed by "---"
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("src:"):
                assert i + 1 < len(lines), f"src: at line {i} has no closing ---"
                assert lines[i + 1].strip() == "---", (
                    f"src: at line {i} not closed: next line is {lines[i+1]!r}"
                )

    def test_style_css_has_slidev_theme_vars(self, deck_output: tuple[int, Path]) -> None:
        """style.css must set --slidev-theme-* variables for light mode."""
        _, out = deck_output
        css = (out / "style.css").read_text(encoding="utf-8")
        assert "--slidev-theme-primary" in css
        assert "--slidev-theme-background" in css

    def test_executive_summary_renders_the_phase_pitch(
        self, deck_output: tuple[int, Path]
    ) -> None:
        """The executive summary slide carries the sold phase's own pitch."""
        _, out = deck_output
        content = (out / "pages" / "02-executive-summary.md").read_text(encoding="utf-8")
        assert "P1 sells its own scope" in content
        assert "P1 bullet" in content

    @intent("INT-ESTIMATEKIT-017")
    def test_deck_refuses_a_phase_without_its_executive_summary(
        self, schedulable_project: Project, tmp_path: Path
    ) -> None:
        """A missing executive summary is refused, never rendered as a placeholder."""
        phase = schedulable_project.phases[0]
        phase.executive_summary = None
        with pytest.raises(PhaseInputMissingError) as excinfo:
            _write(schedulable_project, phase, tmp_path)
        assert "P1-executive-summary.tsv" in str(excinfo.value)

    def test_speaker_notes_rendered(self, schedulable_project: Project, tmp_path: Path) -> None:
        """Speaker notes from the phase's notes file appear as HTML comments."""
        phase = schedulable_project.phases[0]
        phase.slide_notes.append(
            SlideNote(slide="effort", position="speaker", text="Remember to check burn rate.")
        )
        _write(schedulable_project, phase, tmp_path)
        content = (tmp_path / "pages" / "09-effort-estimate.md").read_text(encoding="utf-8")
        assert "<!--" in content
        assert "Remember to check burn rate." in content


class TestTheDeckSellsOnePhase:
    """On a multi-phase project the deck is the named phase's, with the rest as context."""

    @pytest.fixture()
    def two_phase_project(self, minimal_project: Project) -> Project:
        first = minimal_project.phases[0]
        _make_schedulable(first)
        first.executive_summary = _pitch("P1")
        first.components = [
            Component("Web Application", "Frontend", "React", "The P1 portal"),
        ]
        first.slide_notes.append(
            SlideNote(slide="effort", position="speaker", text=_P1_EFFORT_NOTE),
        )
        second = Phase(
            phase_id="P2",
            name="Automation",
            description="Write integrations on the P1 platform",
            phase_name="Phase 2",
            build_activities=[
                BuildActivity(
                    activity_id="B-P2", group="Core", name="Automate",
                    effort_md=12.0, req_ids={RequirementId("REQ-001")},
                ),
            ],
        )
        _make_schedulable(second)
        second.executive_summary = _pitch("P2")
        second.components = [
            Component("Workflow Engine", "Backend", "Temporal", "P2 orchestration"),
            Component("Write Adapter", "Integration", "REST", "P2 write-back"),
        ]
        second.slide_notes.append(
            SlideNote(slide="effort", position="speaker", text=_P2_EFFORT_NOTE),
        )
        minimal_project.phases.append(second)
        minimal_project.guidelines = [
            Guideline("GUIDE-001", "Positioning", "Channel not core", "Always"),
            Guideline(
                "GUIDE-002", "Integration", "Write through adapters", "P2 only",
                phase_ids=frozenset({"P2"}),
            ),
        ]
        return minimal_project

    @intent("INT-ESTIMATEKIT-017")
    def test_architecture_slide_shows_the_sold_phase_not_the_first(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        """INT-ESTIMATEKIT-017: selling P2 renders P2's components, not the first phase's."""
        _write(two_phase_project, two_phase_project.phases[1], tmp_path)
        content = (tmp_path / "pages" / "06-architecture.md").read_text(encoding="utf-8")
        assert "**2 components**" in content
        assert "Workflow Engine" in content or "Backend" in content
        assert "P2" in content

    @intent("INT-ESTIMATEKIT-017")
    def test_executive_summary_is_the_sold_phases(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        _write(two_phase_project, two_phase_project.phases[1], tmp_path)
        content = (tmp_path / "pages" / "02-executive-summary.md").read_text(encoding="utf-8")
        assert "P2 sells its own scope" in content
        assert "P1 sells its own scope" not in content

    @intent("INT-ESTIMATEKIT-017")
    def test_guidelines_are_filtered_to_the_sold_phase(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        _write(two_phase_project, two_phase_project.phases[0], tmp_path)
        content = (tmp_path / "pages" / "06-guidelines-1.md").read_text(encoding="utf-8")
        assert "GUIDE-001" in content
        assert "GUIDE-002" not in content

    @intent("INT-ESTIMATEKIT-017")
    def test_only_the_sold_phase_gets_its_own_sections(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        _write(two_phase_project, two_phase_project.phases[1], tmp_path)
        names = sorted(p.name for p in (tmp_path / "pages").glob("11-*.md"))
        assert names and all(name.endswith("-p2.md") for name in names)
        assert (tmp_path / "pages" / "10a-roadmap-all.md").exists()
        assert (tmp_path / "pages" / "09-effort-estimate.md").exists()

    @intent("INT-ESTIMATEKIT-017")
    def test_title_slide_names_the_sold_phase(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        _write(two_phase_project, two_phase_project.phases[1], tmp_path)
        content = (tmp_path / "slides.md").read_text(encoding="utf-8")
        assert "P2 Effort Estimate: Automation" in content
        assert "Write integrations on the P1 platform" in content

    @intent("INT-ESTIMATEKIT-017")
    def test_speaker_notes_are_the_sold_phases(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        _write(two_phase_project, two_phase_project.phases[1], tmp_path)
        content = (tmp_path / "pages" / "09-effort-estimate.md").read_text(encoding="utf-8")
        assert _P2_EFFORT_NOTE in content
        assert _P1_EFFORT_NOTE not in content

    def test_regenerating_for_another_phase_keeps_only_its_pages(
        self, two_phase_project: Project, tmp_path: Path
    ) -> None:
        """The pages directory holds exactly the pages slides.md imports."""
        _write(two_phase_project, two_phase_project.phases[0], tmp_path)
        _write(two_phase_project, two_phase_project.phases[1], tmp_path)
        pages_dir = tmp_path / "pages"
        slides = (tmp_path / "slides.md").read_text(encoding="utf-8")
        imported = {
            line.removeprefix("src: ./pages/")
            for line in slides.splitlines()
            if line.startswith("src: ./pages/")
        }
        assert not list(pages_dir.glob("*-p1.md"))
        assert imported == {page.name for page in pages_dir.glob("*.md")}


class TestComputePhaseRevenue:
    """VROM revenue computes from raw resource rows with tolerant rate parsing."""

    def test_currency_prefixed_rate_contributes_revenue(self, minimal_phase: Phase) -> None:
        minimal_phase.resource_rows = [
            {
                "Stream": "1.Design", "Profile": "Architect", "Rate Day": "EUR 350",
                "M1": "2", "M2": "1.5",
            },
        ]
        revenue = compute_phase_revenue(minimal_phase, gm_pct=0.0)
        assert revenue == 350.0 * 3.5

    def test_unparsable_rate_raises_invalid_rate_error(self, minimal_phase: Phase) -> None:
        minimal_phase.resource_rows = [
            {"Stream": "1.Design", "Profile": "Architect", "Rate Day": "TBD", "M1": "2"},
        ]
        with pytest.raises(InvalidRateError) as excinfo:
            compute_phase_revenue(minimal_phase)
        assert "TBD" in str(excinfo.value)
