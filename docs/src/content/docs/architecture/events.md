---
title: Events
id: DOC-ESTIMATEKIT-EVENTS-001
type: Reference
status: Active
updated: "2026-08-22"
summary: "The facts EstimateKit states on the platform event bus: one row per type under the estimation domain it owns, with the subject and the pointers each carries. The consumer's contract, held equal to the publisher by a test."
---

EstimateKit owns the `estimation` domain on the platform's event bus by its own grant (the platform's `onboard-events` guide), and states one fact per act that changes a project or cuts an artifact. This page is the contract a consumer reads: the types, what each is about, and what `data` carries. It is held equal to the publisher's constants by the engine's test suite (`test_event_publishing.py`), so a row here is a type the engine emits and nothing else is.

Every event is a CloudEvent with `source` `/foundry/estimatekit` and `datacontenttype` `application/json`. Each carries the project slug and a pointer, never the project's numbers, a file's content, or an audit's findings: the engine stays the store, and a consumer fetches from it by slug. Publishing is one-way (`REF-Events` section 6): a publish that cannot be delivered is dropped and logged, and no audit or generation outcome depends on the broker, which `INT-ESTIMATEKIT-016` attests for every act below.

## The types

| Type | `subject` | Published when | `data` |
|---|---|---|---|
| `com.foundry.estimation.project.scaffolded` | the project slug | a project is scaffolded from the template | `project` |
| `com.foundry.estimation.file.written` | the project slug | a project data file is written | `project`, `path` |
| `com.foundry.estimation.file.deleted` | the project slug | a project data file is removed | `project`, `path` |
| `com.foundry.estimation.audit.completed` | the project slug | the audit suite finishes over a project | `project`, `verdict` (`pass` or `fail`), `passed`, `failed`, `skipped`, `suggestions` (counts) |
| `com.foundry.estimation.artifact.generated` | the project slug | a generation pipeline produces its artifact; one fact per artifact that exists | `project`, `artifact` (`roadmap`, `excel`, `slides`) |
| `com.foundry.estimation.project.renamed` | the new slug | a project's slug or display name changes | `project`, `previous`, `name_changed` |
| `com.foundry.estimation.project.archived` | the project slug | a project leaves the active listing | `project` |
| `com.foundry.estimation.project.unarchived` | the project slug | a project returns to the active listing | `project` |
| `com.foundry.estimation.project.deleted` | the project slug | a project is removed | `project` |

## What is not stated

The audit's findings and suggestions never ride the event; only the verdict and the counts do, and a reader that needs the findings runs or fetches the report. A generation pipeline that failed produced nothing, so nothing is stated for it. Reads (listing, summaries, downloads, diagram renders) change nothing and state nothing.

Adding a type is one change to this page and to `engine/application/events.py` together; the test refuses either alone.
