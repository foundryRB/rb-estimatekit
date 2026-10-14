"""Slide renderer: assumptions overview and risk map."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from engine.adapters.outbound.slidev.renderer import footer, speaker_notes
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project
from engine.domain.model.entities.assumption import Assumption
from engine.domain.model.value_objects.confidence import Confidence
from engine.domain.model.value_objects.impact import Impact
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap

# ── Helpers ─────────────────────────────────────────────────────────────


def _group_assumptions(
    assumptions: list[Assumption],
) -> OrderedDict[str, list[Assumption]]:
    """Group assumptions by .group, preserving encounter order."""
    groups: OrderedDict[str, list[Assumption]] = OrderedDict()
    for a in assumptions:
        groups.setdefault(a.group, []).append(a)
    return groups


def _dash(n: int) -> str:
    """Return '—' for zero, otherwise the number as string."""
    return "—" if n == 0 else str(n)


# ── Slide 1: Assumptions Overview ───────────────────────────────────────


def _render_overview(project: Project, output_dir: Path, *, notes: str = "") -> str | None:
    """Generate 07-assumptions.md. Returns filename or None."""
    if not project.assumptions:
        return None

    groups = _group_assumptions(project.assumptions)

    # Aggregate per-group stats
    conf_totals = {Confidence.HIGH: 0, Confidence.MEDIUM: 0, Confidence.LOW: 0}
    crit_total = 0

    tbl = ""
    for group_name, items in groups.items():
        count = len(items)
        high = sum(1 for a in items if a.confidence == Confidence.HIGH)
        med = sum(1 for a in items if a.confidence == Confidence.MEDIUM)
        low = sum(1 for a in items if a.confidence == Confidence.LOW)
        crit = sum(1 for a in items if a.impact == Impact.CRITICAL)

        conf_totals[Confidence.HIGH] += high
        conf_totals[Confidence.MEDIUM] += med
        conf_totals[Confidence.LOW] += low
        crit_total += crit

        tbl += (
            f"| **{group_name}** | {count} | {_dash(high)} | "
            f"{_dash(med)} | {_dash(low)} | {_dash(crit)} |\n"
        )

    total = len(project.assumptions)

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    conf_line = (
        f"**{total} assumptions** · Confidence:"
        f" HIGH {conf_totals[Confidence.HIGH]}"
        f" · MEDIUM {conf_totals[Confidence.MEDIUM]}"
        f" · LOW {conf_totals[Confidence.LOW]}"
        f" · Critical Impact: {crit_total}"
    )

    content = f"""---
layout: default
---

# Assumptions Overview

<div class="rb-divider"></div>

{conf_line}

<div class="text-xs mt-2">

| Group | Count | High | Med | Low | Crit. |
|---|:---:|:---:|:---:|:---:|:---:|
{tbl}
</div>
{foot}{notes}
"""

    filename = "07-assumptions.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


# ── Slide 2: Assumption Risk Map ────────────────────────────────────────

# Rows one column carries before the slide stops being readable. A column
# holding more says how many it keeps back, so the omission is on the slide
# rather than silent: a register the deck under-reports reads as a small one.
_MAX_ROWS_PER_COLUMN = 12

# IDs the closing line names before it stops being a line and starts being the
# VALIDATE column again. Past this it gives the count and points at the column.
_MAX_TOP_RISKS_NAMED = 6

# Most severe first, so a capped column keeps back its least severe rows.
_IMPACT_ORDER: dict[Impact, int] = {
    Impact.CRITICAL: 0,
    Impact.HIGH: 1,
    Impact.MEDIUM: 2,
    Impact.LOW: 3,
}

_IMPACT_LABEL: dict[Impact, str] = {
    Impact.CRITICAL: "CRIT",
    Impact.HIGH: "HIGH",
    Impact.MEDIUM: "MED",
    Impact.LOW: "LOW",
}

# Confidence picks the column because it names the act; impact orders the rows
# inside it because it names the stake.
_ACTION_BY_CONFIDENCE: dict[Confidence, tuple[str, str]] = {
    Confidence.LOW: ("VALIDATE", "critical"),
    Confidence.MEDIUM: ("MONITOR", "monitor"),
    Confidence.HIGH: ("ACCEPT", "accept"),
}


def _short_desc(a: Assumption) -> str:
    """One-line label for an assumption: its short title, else its truncated text."""
    desc = a.short_title.strip() if a.short_title else ""
    if desc:
        return desc
    desc = a.assumption
    return desc[:27] + "..." if len(desc) > 30 else desc


def _risk_column(action: str, css_suffix: str, items: list[Assumption]) -> str:
    """Render one confidence column: its header, its rows, and what it keeps back."""
    shown = items[:_MAX_ROWS_PER_COLUMN]
    kept_back = len(items) - len(shown)

    if shown:
        body = "| ID | Assumption | Impact |\n|---|---|:---:|\n" + "".join(
            f"| **{a.assumption_id}** | {_short_desc(a)} | "
            f"{_IMPACT_LABEL.get(a.impact, a.impact.value)} |\n"
            for a in shown
        )
    else:
        body = "_None_\n"

    if kept_back:
        body += f"\n_+{kept_back} more, lower impact._\n"

    return f"""<div>

<div style="font-size:0.65rem;">

<div class="rb-risk-header rb-risk-header--{css_suffix}">
{action} ({len(items)})
</div>

{body}
</div>

</div>"""


def _render_risk_map(project: Project, output_dir: Path, *, notes: str = "") -> str | None:
    """Generate 08-assumptions-risk.md. Returns filename or None.

    Every assumption reaches this slide. Confidence picks the column (the act
    the reader owes it) and impact orders the rows within it (what rides on it),
    so a high-stake assumption is visible whatever its tier. The register is the
    signer's exposure, and a slide showing one tier of it reads as the whole
    register while understating the rest.
    """
    if not project.assumptions:
        return None

    buckets: dict[Confidence, list[Assumption]] = {c: [] for c in _ACTION_BY_CONFIDENCE}
    for a in project.assumptions:
        buckets.setdefault(a.confidence, []).append(a)
    for items in buckets.values():
        items.sort(
            key=lambda a: (
                _IMPACT_ORDER.get(a.impact, len(_IMPACT_ORDER)),
                a.assumption_id,
            )
        )

    columns = "\n\n".join(
        _risk_column(action, css_suffix, buckets[confidence])
        for confidence, (action, css_suffix) in _ACTION_BY_CONFIDENCE.items()
    )

    total = len(project.assumptions)
    n_critical = sum(1 for a in project.assumptions if a.impact == Impact.CRITICAL)
    # Same order the VALIDATE column shows, so the two read as one list.
    high_risk = [
        a.assumption_id
        for a in buckets[Confidence.LOW]
        if a.is_high_risk
    ]

    if len(high_risk) > _MAX_TOP_RISKS_NAMED:
        named = ", ".join(high_risk[:_MAX_TOP_RISKS_NAMED])
        rest = len(high_risk) - _MAX_TOP_RISKS_NAMED
        risk_note = (
            f"**Top risks:** {len(high_risk)} assumptions pair low confidence with a "
            f"high stake, starting {named} and {rest} more in VALIDATE. Validate them "
            "with stakeholders before signature."
        )
    elif high_risk:
        risk_note = (
            f"**Top risks:** {', '.join(high_risk)}. Low confidence against a high "
            "stake, so validate these with stakeholders before signature."
        )
    else:
        risk_note = (
            "**Top risks:** none. No assumption pairs low confidence with a high "
            "stake; the VALIDATE column is still the one to work first."
        )

    cfg = project.config
    foot = footer(cfg.name, cfg.branding.company)

    content = f"""---
layout: default
---

# Assumption Risk Map

<div class="rb-divider"></div>

**All {total} assumptions**, by confidence (the act) and impact (the stake)
· {n_critical} of critical impact.

<div class="grid grid-cols-3 gap-2 mt-1">

{columns}

</div>

<div class="rb-note mt-1">

{risk_note}

</div>
{foot}{notes}
"""

    filename = "08-assumptions-risk.md"
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / filename).write_text(content, encoding="utf-8")
    return filename


# ── Public entry point ──────────────────────────────────────────────────


def render(
    project: Project,
    phase: Phase,
    efforts: dict[str, PhaseEffort],
    roadmaps: list[PhaseRoadmap],
    output_dir: Path,
) -> list[str]:
    """Generate assumptions overview + risk map slides. Returns filenames."""
    written: list[str] = []
    notes = speaker_notes(phase, "assumptions")
    for gen in (_render_overview, _render_risk_map):
        fname = gen(project, output_dir, notes=notes)
        if fname:
            written.append(fname)
    return written
