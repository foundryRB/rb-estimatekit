"""ResourcePlan — monthly staffing capacity per stream."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ResourcePlan"]


@dataclass(frozen=True)
class ResourcePlan:
    """Monthly staffing capacity per stream."""

    streams: dict[str, list[float]] = field(default_factory=dict)
    # stream_name → [month_1_capacity, month_2_capacity, …]

    @property
    def n_months(self) -> int:
        """Number of months in the plan."""
        if not self.streams:
            return 0
        return max(len(v) for v in self.streams.values())

    @property
    def total_capacity(self) -> float:
        """Sum of all stream capacities across all months."""
        return sum(sum(months) for months in self.streams.values())

    def stream_total(self, stream: str) -> float:
        """Total capacity for a single stream."""
        return sum(self.streams.get(stream, []))
