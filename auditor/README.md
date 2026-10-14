# Auditor

> Validates project data integrity — ensures a human filled in the estimation files correctly.

---

## What This Is

The Auditor is a **separate application** from the engine. While the engine generates outputs (roadmaps, Excel, slides), the Auditor validates that the input data for those outputs is correct, consistent, and complete.

**These are not software tests.** Software tests verify that *our code* works. Data checks verify that *the user's data* is correct.

---

## Quick Start

```bash
# Run all checks against the default project
python -m pytest auditor/ -v

# Run checks against a specific project
ESTIMATEKIT_PROJECT=projects/demo-acme python -m pytest auditor/ -v

# Run a single category
python -m pytest auditor/checks/brd/ -v

# Run a single check
python -m pytest auditor/checks/tsv/test_validity.py::test_all_tsv_files_are_valid_utf8 -v
```

---

## Follow-on phase scope

An explicit phase audit runs that phase's content and per-phase roadmap checks,
plus the project's shared integrity checks. Requirement IDs, matrix definitions,
activity-ID overlap, cross-phase references, TSV structure, shared source coverage,
and All-phases roadmap consistency remain checked across the project.

```bash
estimatekit audit projects/example --phase P2
ESTIMATEKIT_PROJECT=projects/example python -m pytest auditor/ --phase P2 -v
```

The HTTP entry point accepts `POST /api/projects/{slug}/audit?phase=P2`; the MCP
`run_audit` tool accepts `phase: "P2"`. Each engine report identifies its `phase`;
`null` means the whole project. Omitting the selector runs the whole project, and
an undefined phase is refused. Risk suggestions retain their project-wide advisory
context and do not decide the verdict.

A passing scoped audit supports the selected phase's proposal and artifacts. Prior
phases remain historical context: this result does not assert that their capacity,
content or individual roadmap checks passed the current rules.

## Check Categories

| Category | What It Validates |
|----------|-------------------|
| `tsv/` | Structural TSV integrity — UTF-8 encoding, consistent column counts, correct headers |
| `brd/` | BRD and customer requirements: every non-blank line of the requirements cited by a BRD row, no duplicate Req IDs, valid line references |
| `consistency/` | Cross-file consistency: the BRD and the matrix hold the same Req IDs, and besides Category, Req ID, Description and Notes the matrix holds exactly one column per defined phase |
| `activity/` | Activity data: capacity ≥ effort per stream, no resource line over 20 md in a month, requirement coverage, no duplicates, valid and well-formed Req IDs (comma-separated, or `All` alone), timeline feasibility, effort totals |
| `assumptions/` | Assumptions integrity: no duplicate IDs, valid Confidence/Impact values, valid Req ID references in well-formed cells |
| `phase/` | Phase reporting: requirements-per-phase breakdown, multi-phase item detection; no `P<n>-` file under `data/` for a phase the phase table does not define |
| `reverse/` | Scope creep detection — Build activities must only reference requirements assigned to their phase |
| `architecture/` | Per-phase architecture: every defined phase has an overview diagram and a non-empty component inventory whose components the diagram names; the guidelines declare `Phase IDs`, every value is `All` or a defined phase, and every phase has at least one governing guideline |
| `scaffold/` | No scaffold sentinel (`[EXAMPLE]`, `[PROJECT NAME]`, `[Client Name]`) remains in `project.yaml` or under `data/` |
| `slides/` | Per-phase pitch copy: every defined phase has a `P<n>-executive-summary.tsv` with a context description, and `slides/` holds nothing but defined phases' executive summaries and notes |

---

## Architecture

The Auditor intentionally does **not** use hexagonal architecture. Each check reads data files directly and asserts rules. There's no complex orchestration or adapter layer to justify the indirection.

```
auditor/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures (project_root, config, phases)
├── helpers.py               # skip/fail helpers
├── activities.py            # Activity file reading
├── config.py                # Project configuration loading
├── helpers.py               # skip/fail helpers
├── phases.py                # Phase discovery
├── project.py               # Project root resolution and path helpers
├── requirements.py          # Requirement ID parsing and matrix reading
├── tsv.py                   # TSV reading primitives
└── checks/
    ├── tsv/                 # Structural checks
    ├── brd/                 # BRD checks
    ├── consistency/         # Cross-file checks
    ├── activity/            # Activity checks
    ├── assumptions/         # Assumptions checks
    ├── phase/               # Phase reporting and phase-file orphans
    ├── reverse/             # Reverse coverage
    ├── architecture/        # Per-phase architecture and guideline scoping
    ├── scaffold/            # Scaffold sentinels
    └── slides/              # Per-phase pitch copy
```

Key design decisions:

- **Self-contained modules:** The auditor has its own data I/O. Of the engine it imports only the domain constants (`engine.domain.constants`), so a rule both apply, such as which streams are test streams (`is_qa_stream`), has one definition; it never imports the engine's application or adapter code.
- **pytest as runner:** Checks use `test_` prefix for pytest discovery, but they validate data, not code.
- **Independent categories:** Each folder can run standalone (`python -m pytest auditor/checks/brd/`).
- **Session-scoped fixtures:** Project data is loaded once per session, shared across all checks.
- **Dynamic parametrization:** Phase-dependent checks are auto-parametrized from the phase-definitions file (`data/requirements/02-phases.tsv`).
- **Missing files are check outcomes, not crashes:** a missing input file fails the affected checks with a message naming the file; missing generated roadmap output (regenerated, gitignored) skips its checks. Collection never aborts on absent data.

---

## Adding a New Check

1. Identify the category (or create a new folder under `checks/`).
2. Create `test_<concern>.py` — one file per rule or closely related rule set.
3. Use the fixtures from `conftest.py`: `project_root`, `config`, `data_dir`, `phase` (for per-phase checks).
4. Import from the semantic modules (`auditor.tsv`, `auditor.project`, etc.); from the engine, import only its domain constants (`engine.domain.constants`).
5. Use `auditor.helpers` for `skip_unless_feature_enabled` / `fail_if_file_missing`.

```python
"""Description of what this check validates."""

from __future__ import annotations

import logging
from pathlib import Path

from auditor.project import get_data_file
from auditor.tsv import read_tsv

logger = logging.getLogger(__name__)


def test_my_new_rule(project_root: Path) -> None:
    """One-line description of the rule."""
    path = get_data_file(project_root, "SomeFile.tsv")
    rows = read_tsv(path)
    failures = [...]  # collect violations
    assert not failures, f"Found {len(failures)} violations:\n" + "\n".join(failures)
```

---

## How It Differs From Software Tests

| | Software Tests (`engine/tests/`) | Data Checks (`auditor/checks/`) |
|---|---|---|
| **Subject** | Our code (engine) | User's data (project TSVs) |
| **Changes when** | Code changes | Project data changes |
| **Fixed input** | Test fixtures (synthetic) | Real project files |
| **Fixed logic** | The code under test | The validation rules |
| **Failure means** | Bug in our code | Error in data entry |
| **Run when** | Development, CI | After data authoring |
