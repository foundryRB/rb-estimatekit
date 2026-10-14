"""TSV writers for individual roadmap views (per-phase)."""

from __future__ import annotations

import csv
from pathlib import Path

from engine.adapters.outbound.roadmap.helpers import last_true, order_cats
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

__all__ = [
    "write_activity_groups",
    "write_build",
    "write_lifecycle",
    "write_resource",
]


def write_resource(
    out_dir: Path, phase: str,
    stream_caps: dict[str, list[float]], labels: list[str],
) -> None:
    """Write Roadmap-Resource{phase}.tsv."""
    path = out_dir / f"Roadmap-Resource{phase}.tsv"
    ordered = sorted(stream_caps.keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Stream", "Total (MD)", *labels])
        total_row = [0.0] * len(labels)
        for stream in ordered:
            caps = stream_caps[stream]
            total = round(sum(caps))
            w.writerow([stream, total, *[str(round(c)) for c in caps]])
            for i, c in enumerate(caps):
                total_row[i] += c
        w.writerow(["TOTAL", round(sum(total_row)),
                    *[str(round(t)) for t in total_row]])


def write_activity_groups(
    out_dir: Path, phase: str, groups: list, labels: list[str],
) -> None:
    """Write Roadmap-ActivityGroup{phase}.tsv."""
    path = out_dir / f"Roadmap-ActivityGroup{phase}.tsv"
    n = len(labels)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Activity Group", "Stream", "Effort (MD)", "Milestone", *labels])
        for g in groups:
            cells = []
            for m in range(n):
                if m == g.end_month:
                    cells.append("◆")
                elif g.start_month <= m < g.end_month:
                    cells.append("·")
                else:
                    cells.append("")
            w.writerow([g.name, g.stream, round(g.effort),
                        f"{g.name} Complete", *cells])
        # Footer — active counts
        counts = [str(sum(1 for g in groups
                          if g.start_month <= m <= g.end_month))
                  for m in range(n)]
        w.writerow(["", "", "", "Active Groups", *counts])


def write_build(out_dir: Path, phase: str, rm: PhaseRoadmap) -> None:
    """Write Roadmap-Build{phase}.tsv."""
    path = out_dir / f"Roadmap-Build{phase}.tsv"
    ordered = order_cats(rm.build_active, rm.build.rows)
    labels = rm.month_labels
    n = len(labels)

    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Category", "Effort (MD)", "Milestone", *labels])
        for cat in ordered:
            effort = round(rm.effort_by_cat.get(cat, 0))
            flags = rm.build_active.get(cat, [False] * n)
            last = last_true(flags)
            cells = []
            for i in range(n):
                if i < len(flags) and flags[i]:
                    cells.append("◆" if i == last else "·")
                else:
                    cells.append("")
            w.writerow([cat, effort, f"{cat} Complete", *cells])
        # Footer
        mc = [str(sum(1 for cat in ordered
                      if last_true(rm.build_active.get(cat, [])) == m))
              for m in range(n)]
        w.writerow(["", "", "Milestones", *mc])


def write_lifecycle(out_dir: Path, phase: str, rm: PhaseRoadmap) -> None:
    """Write Roadmap-Lifecycle{phase}.tsv."""
    ordered = order_cats(rm.lifecycle_raw, rm.lifecycle.rows)
    base_labels = rm.month_labels
    max_len = max((len(c) for c in rm.lifecycle_raw.values()),
                  default=len(base_labels))
    labels = list(base_labels)
    for i in range(len(labels), max_len):
        labels.append(f"M{i + 1}")
    n = len(labels)

    path = out_dir / f"Roadmap-Lifecycle{phase}.tsv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Category", "Effort (MD)", "Milestone", *labels])
        for cat in ordered:
            effort = round(rm.effort_by_cat.get(cat, 0))
            cells_data = rm.lifecycle_raw.get(cat, [])
            cells = [cells_data[i] if i < len(cells_data) else ""
                     for i in range(n)]
            w.writerow([cat, effort, f"{cat} Complete", *cells])
        mc = [str(sum(1 for cat in ordered
                      if i < len(rm.lifecycle_raw.get(cat, []))
                      and rm.lifecycle_raw[cat][i] == "◆"))
              for i in range(n)]
        w.writerow(["", "", "Milestones", *mc])
