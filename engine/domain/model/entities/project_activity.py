"""ProjectActivity — an overhead / project management activity."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ProjectActivity"]


@dataclass
class ProjectActivity:
    """An overhead / project management activity outside the build."""

    group: str                      # "Design Lead", "Project Management"
    stream: str                     # "Management", "Architecture"
    effort_md: float

    @property
    def is_build_detailed(self) -> bool:
        """Whether the Build register already itemises this row's effort.

        The project register carries every stream's authored effort, and the
        Build register details two of those rows activity by activity: the
        ``Build Activities`` group and whatever sits in a Design stream. Those
        two are the build total seen from the project side, so counting them
        again as overhead would bill the same work twice. ``Build Activities``
        is the only fixed name; everything else resolves through the Stream
        column, which is the same convention the auditor's project-totals check
        asserts the data against.
        """
        return (
            self.group.strip().lower().startswith("build activit")
            or "design" in self.stream.lower()
        )
