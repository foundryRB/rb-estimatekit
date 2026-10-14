"""Project configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

__all__ = ["has_feature", "load_config"]


def load_config(project_root: Path) -> dict[str, Any]:
    """Load ``project.yaml`` from *project_root*.

    A missing file fails the calling check with a message naming the file.
    """
    config_path = project_root / "project.yaml"
    if not config_path.exists():
        pytest.fail(f"Required project file missing: {config_path}", pytrace=False)
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def has_feature(config: dict[str, Any], feature_name: str) -> bool:
    """Return ``True`` if *feature_name* is enabled in the ``features`` map."""
    features = config.get("features", {})
    return bool(features.get(feature_name, False))
