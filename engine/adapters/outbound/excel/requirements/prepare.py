"""Extract all requirements data into plain structures."""

from __future__ import annotations

from engine.domain.model.aggregates.project import Project

from .models import (
    CategorySummaryRow,
    EffortRow,
    PhaseOverviewRow,
    ReqMatrixRow,
    RequirementsData,
)


def prepare_requirements(project: Project) -> RequirementsData | None:
    """Extract all requirements data into plain structures. No openpyxl."""
    if not project.requirements:
        return None

    phases = project.phases
    reqs = project.requirements
    total_reqs = len(reqs)
    req_counts = project.count_requirements_per_phase()
    categories = project.discover_categories()

    phase_ids = [p.phase_id for p in phases]
    phase_names = [p.phase_name or p.name for p in phases]

    # Phase overview
    phase_overview = []
    for phase in phases:
        cnt = req_counts.get(phase.phase_id, 0)
        pct = round(cnt / total_reqs * 100) if total_reqs else 0
        phase_overview.append(PhaseOverviewRow(
            name=phase.name,
            req_label=f"{cnt}/{total_reqs} ({pct}%)",
            description=phase.description,
        ))

    # Effort rows
    effort_rows = []
    grand_build = 0.0
    grand_overhead = 0.0
    grand_total_val = 0.0
    for phase in phases:
        effort = phase.compute_effort()
        build = effort.build_total
        overhead = effort.overhead_total
        total = effort.authored_total
        effort_rows.append(EffortRow(name=phase.name, build=build, overhead=overhead, total=total))
        grand_build += effort.build_total
        grand_overhead += effort.overhead_total
        grand_total_val += effort.authored_total

    # Requirements matrix grouped by category
    req_groups: list[tuple[str, list[ReqMatrixRow]]] = []
    for cat in categories:
        cat_reqs = [r for r in reqs if r.category.name == cat.name]
        if not cat_reqs:
            continue
        rows = []
        for req in cat_reqs:
            allocs: dict[str, str] = {}
            for phase in phases:
                alloc = req.phase_allocations.get(phase.phase_id, "").strip()
                allocs[phase.phase_id] = alloc
            rows.append(ReqMatrixRow(
                req_id=str(req.id),
                description=req.description,
                phase_allocations=allocs,
            ))
        req_groups.append((cat.display_name, rows))

    # Category summary
    cat_summaries = []
    for cat in categories:
        cat_reqs = [r for r in reqs if r.category.name == cat.name]
        phase_counts: dict[str, int] = {}
        for phase in phases:
            phase_counts[phase.phase_id] = sum(
                1 for req in cat_reqs if req.is_allocated_to(phase.phase_id)
            )
        cat_summaries.append(CategorySummaryRow(
            display_name=cat.display_name,
            total=len(cat_reqs),
            phase_counts=phase_counts,
        ))

    return RequirementsData(
        project_name=project.config.name,
        project_description=project.config.description,
        total_reqs=total_reqs,
        phase_names=phase_names,
        phase_ids=phase_ids,
        phase_overview=phase_overview,
        effort_rows=effort_rows,
        grand_build=grand_build,
        grand_overhead=grand_overhead,
        grand_total=grand_total_val,
        categories=[c.display_name for c in categories],
        req_groups=req_groups,
        category_summaries=cat_summaries,
    )
