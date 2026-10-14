"""ProjectConfig — top-level project identity from project.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.branding import BrandConfig

__all__ = ["ProjectConfig"]


@dataclass(frozen=True)
class ProjectConfig:
    """Top-level project identity from project.yaml."""

    name: str                       # "VFPT Local M2M"
    short_name: str                 # "Local M2M"
    client: str                     # "Vodafone Portugal"
    author: str                     # "Vodafone Portugal"
    description: str                # "IoT Connectivity Management Platform"
    date: str                       # "February 2026"
    branding: BrandConfig = field(default_factory=BrandConfig)
    features: dict[str, bool] = field(default_factory=dict)

    def has_feature(self, name: str) -> bool:
        """Check whether a feature flag is enabled."""
        return self.features.get(name, False)
