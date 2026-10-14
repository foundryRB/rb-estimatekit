"""Shared test fixtures — synthetic project builders."""

from __future__ import annotations

import os

import pytest

from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.assumption import Assumption
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.entities.requirement import Requirement
from engine.domain.model.value_objects.branding import BrandConfig
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.confidence import Confidence
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.impact import Impact
from engine.domain.model.value_objects.phase_config import PhaseConfig
from engine.domain.model.value_objects.requirement_id import RequirementId
from engine.domain.model.value_objects.resource_plan import ResourcePlan

# The HTTP adapter gates every route behind fail-closed Basic auth
# (engine/adapters/inbound/http/auth.py). Disable it for the suite so integration
# tests hit the routes directly; test_auth.py re-enables it per-test to assert the gate.
os.environ.setdefault("ESTIMATEKIT_AUTH_DISABLED", "true")


@pytest.fixture
def brand() -> BrandConfig:
    return BrandConfig(primary_color="#E60000", company="TestCorp")


@pytest.fixture
def config(brand: BrandConfig) -> ProjectConfig:
    return ProjectConfig(
        name="Test Project",
        short_name="Test",
        client="Test Client",
        author="TestCorp",
        description="A test project",
        date="January 2026",
        branding=brand,
    )


@pytest.fixture
def minimal_phase() -> Phase:
    """A single phase with a small number of activities."""
    return Phase(
        phase_id="P1",
        name="Phase 1",
        description="First phase",
        build_activities=[
            BuildActivity(
                activity_id="B001",
                group="Core",
                name="Implement feature A",
                effort_md=10.0,
                req_ids={RequirementId("REQ-001")},
            ),
            BuildActivity(
                activity_id="B002",
                group="Core",
                name="Implement feature B",
                effort_md=5.0,
                req_ids={RequirementId("REQ-002")},
            ),
            BuildActivity(
                activity_id="B003",
                group="Integration",
                name="API integration",
                effort_md=8.0,
                req_ids={RequirementId("REQ-001"), RequirementId("REQ-003")},
            ),
        ],
        project_activities=[
            ProjectActivity(group="Project Management", stream="Management", effort_md=15.0),
            ProjectActivity(group="Design Lead", stream="Architecture", effort_md=10.0),
        ],
        resource_plan=ResourcePlan(
            streams={
                "Development": [2.0, 2.0, 2.0, 1.0],
                "Management": [0.5, 0.5, 0.5, 0.5],
                "Architecture": [1.0, 0.5, 0.0, 0.0],
            }
        ),
        config=PhaseConfig(design_lead_days=20.0, sit_days=20.0, uat_days=20.0),
    )


@pytest.fixture
def minimal_project(config: ProjectConfig, minimal_phase: Phase) -> Project:
    """A minimal project with 1 phase and 3 requirements."""
    return Project(
        config=config,
        phases=[minimal_phase],
        requirements=[
            Requirement(
                id=RequirementId("REQ-001"),
                category=Category(name="Authentication"),
                description="User login",
                phase_allocations={"P1": "Full"},
            ),
            Requirement(
                id=RequirementId("REQ-002"),
                category=Category(name="Authentication"),
                description="Password reset",
                phase_allocations={"P1": "Full"},
            ),
            Requirement(
                id=RequirementId("REQ-003"),
                category=Category(name="Integration"),
                description="External API",
                phase_allocations={"P1": "Partial"},
            ),
        ],
        assumptions=[
            Assumption(
                assumption_id="A001",
                group="Technical",
                assumption="API is stable",
                short_title="Stable API",
                confidence=Confidence.HIGH,
                impact=Impact.MEDIUM,
            ),
        ],
    )
