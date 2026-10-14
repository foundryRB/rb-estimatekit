"""PhaseEffort — computed effort breakdown for a single phase."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.domain.model.value_objects.group_effort import GroupEffort

__all__ = ["PhaseEffort"]


@dataclass(frozen=True)
class PhaseEffort:
    """Computed effort breakdown for a single phase.

    Two quantities, deliberately separate because they answer different
    questions and are never equal by accident:

    - **authored effort** (``build_total`` + ``overhead_total``): what the
      estimate says the work costs. Its split into build and overhead is
      exhaustive and disjoint, so the two operands sum to the total.
    - **staffed capacity** (``staffed_capacity``): what the resource plan books
      to deliver it. The auditor requires capacity to cover effort, so it sits
      at or above the authored total by design.

    A reader that prints one as the sum of the other's parts states an
    arithmetic that does not close; name which of the two is being shown.
    """

    build_total: float
    overhead_total: float
    staffed_capacity: float         # From the resource plan (booked man-days)
    build_groups: dict[str, GroupEffort] = field(default_factory=dict)
    overhead_rows: list[tuple[str, float]] = field(default_factory=list)

    @property
    def authored_total(self) -> float:
        """Total authored effort: the build split and the overhead split, summed."""
        return self.build_total + self.overhead_total

    @property
    def build_group_count(self) -> int:
        """Number of distinct build groups."""
        return len(self.build_groups)
