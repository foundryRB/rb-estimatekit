"""ProjectSlug — the validated containment boundary for project access.

Attests INT-ESTIMATEKIT-004: ProjectSlug validates against
``^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`` at construction and raises
``InvalidSlugError`` on path separators or traversal, so an API caller cannot
escape ``ESTIMATEKIT_PROJECTS_ROOT`` to read or overwrite arbitrary files.
"""

from __future__ import annotations

import pytest
from pytest_intent import intent

from engine.domain.exceptions import InvalidSlugError
from engine.domain.model.value_objects.project_slug import ProjectSlug


@intent("INT-ESTIMATEKIT-004")
def test_project_slug_validates_and_rejects_traversal() -> None:
    """INT-ESTIMATEKIT-004: valid slugs construct; separators / traversal are rejected."""
    # Valid slugs round-trip unchanged.
    assert str(ProjectSlug("acme")) == "acme"
    assert str(ProjectSlug("Acme-2026_v1")) == "Acme-2026_v1"
    assert ProjectSlug("a") == ProjectSlug("a")

    # Path separators and traversal must raise — these are the escape attempts
    # the containment boundary exists to stop.
    for bad in ("../etc", "a/b", "a\\b", "..", "./x", "/abs", "a/../b"):
        with pytest.raises(InvalidSlugError):
            ProjectSlug(bad)


def test_project_slug_rejects_empty_and_leading_separator() -> None:
    """An empty slug or one starting with a non-alphanumeric is rejected."""
    with pytest.raises(InvalidSlugError):
        ProjectSlug("")
    with pytest.raises(InvalidSlugError):
        ProjectSlug("-leading-dash")
    with pytest.raises(InvalidSlugError):
        ProjectSlug("_leading-underscore")


def test_project_slug_enforces_length_bound() -> None:
    """The 64-char ceiling from the pattern is enforced."""
    assert str(ProjectSlug("a" * 64)) == "a" * 64
    with pytest.raises(InvalidSlugError):
        ProjectSlug("a" * 65)
