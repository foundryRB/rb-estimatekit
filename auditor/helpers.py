"""Shared check helpers — importable by any check module.

These are plain functions, not pytest fixtures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from auditor.config import has_feature

__all__ = [
    "fail_if_file_missing",
    "skip_unless_feature_enabled",
]


def skip_unless_feature_enabled(config: dict[str, Any], feature_name: str) -> None:
    """Skip the calling check if *feature_name* is disabled in ``project.yaml``."""
    if not has_feature(config, feature_name):
        pytest.skip(f"Feature '{feature_name}' not enabled in project.yaml")


def fail_if_file_missing(filepath: Path, description: str = "file") -> None:
    """Fail (not skip) when a feature is enabled but its data file is missing.

    Use *after* ``skip_unless_feature_enabled`` — if the feature is on, a
    missing file is a real error, not something to silently skip.
    """
    if not filepath.exists():
        pytest.fail(f"{description} not found: {filepath.name}")
