"""RequirementId — stable identifier for a requirement."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["RequirementId"]


@dataclass(frozen=True)
class RequirementId:
    """Stable identifier for a requirement, e.g. 'AUTH-001'."""

    value: str

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)
