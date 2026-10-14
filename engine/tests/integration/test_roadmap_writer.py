"""Integration tests for TsvRoadmapWriter.

Verifies the roadmap writer produces correct TSV files from in-memory
domain objects, writing to a temporary directory.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from pytest_intent import intent

from engine.adapters.outbound.roadmap.tsv_roadmap_writer import TsvRoadmapWriter
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap
from engine.domain.model.value_objects.resource_plan import ResourcePlan


class TestTsvRoadmapWriter:
    """End-to-end tests for TsvRoadmapWriter using minimal fixtures."""

    @pytest.fixture()
    def schedulable_phase(self, minimal_phase: Phase) -> Phase:
        """Patch minimal_phase with convention-named streams and BRD mappings.

        Streams use the numbered '2.Dev*' convention so build capacity comes
        from the dev stream; brd_order / req_to_category map build activities
        to BRD categories.
        """
        minimal_phase.resource_plan = ResourcePlan(
            streams={
                "2.Dev Backend": [2.0, 2.0, 2.0, 1.0],
                "3.PM": [0.5, 0.5, 0.5, 0.5],
                "1.Arch": [1.0, 0.5, 0.0, 0.0],
            }
        )
        minimal_phase.project_activities = [
            ProjectActivity(group="Build Activities", stream="2.Dev Backend", effort_md=15.0),
            ProjectActivity(group="Design Lead", stream="1.Arch", effort_md=10.0),
        ]
        minimal_phase.brd_order = ["Authentication", "Integration"]
        minimal_phase.req_to_category = {
            "REQ-001": "Authentication",
            "REQ-002": "Authentication",
            "REQ-003": "Integration",
        }
        return minimal_phase

    @pytest.fixture()
    def roadmap(self, schedulable_phase: Phase) -> PhaseRoadmap:
        """Schedule a roadmap from the patched phase fixture."""
        return schedulable_phase.schedule_roadmap()

    @pytest.fixture()
    def output_dir(self, tmp_path: Path, roadmap: PhaseRoadmap) -> Path:
        """Write the roadmap and return the output directory."""
        TsvRoadmapWriter().write_phase(tmp_path, roadmap)
        return tmp_path

    @intent("INT-ESTIMATEKIT-003")
    def test_four_tsv_files_exist(self, output_dir: Path) -> None:
        """All four expected TSV files must be present.

        INT-ESTIMATEKIT-003: the writer is handed an in-memory ``PhaseRoadmap``
        domain object (built from the ``Phase`` fixture via ``schedule_roadmap``),
        not a file path, and renders the output files from it — generation
        receives domain entities, project content comes from the data fixtures.
        """
        expected = [
            "Roadmap-ResourceP1.tsv",
            "Roadmap-ActivityGroupP1.tsv",
            "Roadmap-BuildP1.tsv",
            "Roadmap-LifecycleP1.tsv",
        ]
        for name in expected:
            assert (output_dir / name).exists(), f"Missing file: {name}"

    def test_resource_tsv_has_correct_headers(self, output_dir: Path) -> None:
        """The resource TSV must start with Stream and Total (MD) columns."""
        path = output_dir / "Roadmap-ResourceP1.tsv"
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)
        assert header[0] == "Stream"
        assert header[1] == "Total (MD)"

    def test_activity_group_tsv_has_correct_headers(self, output_dir: Path) -> None:
        """The activity group TSV must have the expected header row."""
        path = output_dir / "Roadmap-ActivityGroupP1.tsv"
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)
        assert "Activity Group" in header
        assert "Stream" in header
        assert "Effort (MD)" in header
        assert "Milestone" in header

    def test_resource_tsv_has_content_rows(self, output_dir: Path) -> None:
        """The resource TSV must have data rows beyond the header."""
        path = output_dir / "Roadmap-ResourceP1.tsv"
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)
        # Header + at least one stream + TOTAL row
        assert len(rows) >= 3

    def test_build_tsv_is_non_empty(self, output_dir: Path) -> None:
        """The build TSV must contain at least a header and one data row."""
        path = output_dir / "Roadmap-BuildP1.tsv"
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)
        assert len(rows) >= 2

    def test_lifecycle_tsv_is_non_empty(self, output_dir: Path) -> None:
        """The lifecycle TSV must contain at least a header and one data row."""
        path = output_dir / "Roadmap-LifecycleP1.tsv"
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)
        assert len(rows) >= 2

    def test_resource_streams_match_fixture(self, output_dir: Path) -> None:
        """The resource TSV must list the three streams from the fixture."""
        path = output_dir / "Roadmap-ResourceP1.tsv"
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)
        stream_names = {row[0] for row in rows[1:] if row[0] != "TOTAL"}
        assert "2.Dev Backend" in stream_names
        assert "3.PM" in stream_names
        assert "1.Arch" in stream_names
