"""Requirement domain service — parsing and discovery functions."""

from __future__ import annotations

from collections.abc import Iterable

from engine.domain.model.entities.requirement import Requirement
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.requirement_id import RequirementId

__all__ = ["discover_categories", "parse_req_ids"]


def parse_req_ids(raw: str) -> set[RequirementId]:
    """Parse a comma-separated requirement ID string into a set.

    ``All`` alone (any case) reads as ``{RequirementId("ALL")}``, the
    cross-cutting sentinel.
    """
    if not raw or not raw.strip():
        return set()
    if raw.strip().upper() == "ALL":
        return {RequirementId("ALL")}
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return {RequirementId(p) for p in parts}


def discover_categories(requirements: Iterable[Requirement]) -> list[Category]:
    """Return unique categories in encounter order."""
    seen: set[str] = set()
    result: list[Category] = []
    for req in requirements:
        if req.category.name not in seen:
            seen.add(req.category.name)
            result.append(req.category)
    return result
