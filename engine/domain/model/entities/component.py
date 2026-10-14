"""Component — a technical component in the architecture."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Component"]


@dataclass
class Component:
    """A technical component in the architecture for a specific phase."""

    name: str
    layer: str                  # "Presentation", "Business", "Data"
    technology: str             # "React", "Spring Boot", "PostgreSQL"
    description: str
