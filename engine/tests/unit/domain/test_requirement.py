"""Tests for Requirement entity."""

from __future__ import annotations

from engine.domain.model.entities.requirement import Requirement
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.requirement_id import RequirementId
from engine.domain.services.requirement_service import discover_categories, parse_req_ids


class TestParseReqIds:
    """parse_req_ids() behavior."""

    def test_empty_string(self) -> None:
        assert parse_req_ids("") == set()

    def test_single_id(self) -> None:
        assert parse_req_ids("AUTH-001") == {RequirementId("AUTH-001")}

    def test_multiple_ids(self) -> None:
        result = parse_req_ids("AUTH-001, SIM-002, IOT-003")
        assert result == {
            RequirementId("AUTH-001"),
            RequirementId("SIM-002"),
            RequirementId("IOT-003"),
        }

    def test_strips_whitespace(self) -> None:
        result = parse_req_ids("  AUTH-001 ,  SIM-002  ")
        assert RequirementId("AUTH-001") in result
        assert RequirementId("SIM-002") in result


class TestRequirementAllocation:
    """Requirement.is_allocated_to() behavior."""

    def test_allocated(self) -> None:
        req = Requirement(
            id=RequirementId("R1"),
            category=Category(name="Test"),
            description="Test",
            phase_allocations={"P1": "Full"},
        )
        assert req.is_allocated_to("P1") is True

    def test_not_allocated(self) -> None:
        req = Requirement(
            id=RequirementId("R1"),
            category=Category(name="Test"),
            description="Test",
            phase_allocations={"P1": "Full"},
        )
        assert req.is_allocated_to("P2") is False

    def test_dash_means_not_allocated(self) -> None:
        req = Requirement(
            id=RequirementId("R1"),
            category=Category(name="Test"),
            description="Test",
            phase_allocations={"P1": "—"},
        )
        assert req.is_allocated_to("P1") is False


class TestDiscoverCategories:
    """discover_categories() behavior."""

    def test_preserves_encounter_order(self) -> None:
        reqs = [
            Requirement(id=RequirementId("R1"), category=Category(name="B"), description=""),
            Requirement(id=RequirementId("R2"), category=Category(name="A"), description=""),
            Requirement(id=RequirementId("R3"), category=Category(name="B"), description=""),
        ]
        cats = discover_categories(reqs)
        assert [c.name for c in cats] == ["B", "A"]
