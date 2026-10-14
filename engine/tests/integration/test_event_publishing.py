"""INT-ESTIMATEKIT-016: publishing is one-way. With the bus unreachable, every act
that would publish completes with the same outcome, the same result, and the same
state on disk as it does with the bus up, each dropped publish is logged, and every
fact is one row of the engine's own events page."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree

import pytest
from pytest_intent import intent

from engine.adapters.outbound.events.publisher import SOURCE, LoggingEventPublisher, cloud_event
from engine.application import events as vocabulary
from engine.application.events import (
    ARTIFACT_GENERATED,
    AUDIT_COMPLETED,
    FILE_DELETED,
    FILE_WRITTEN,
    PROJECT_ARCHIVED,
    PROJECT_DELETED,
    PROJECT_RENAMED,
    PROJECT_SCAFFOLDED,
    PROJECT_UNARCHIVED,
    state_fact,
)
from engine.application.use_cases.run_audit import RunAudit
from engine.container import Container
from engine.domain.model.value_objects.audit_report import AuditReport
from engine.domain.model.value_objects.pipeline import Pipeline


class RecordingPublisher:
    """A bus that is up. It builds the real envelope before recording, so a payload
    the adapter could not serialize fails here instead of being dropped in production."""

    def __init__(self) -> None:
        self.published: list[tuple[str, str, dict]] = []

    def publish(self, *, event_type, subject, data) -> None:
        cloud_event(event_type=event_type, subject=subject, data=data)
        self.published.append((event_type, subject, data))

    @property
    def types(self) -> list[str]:
        return [t for t, _s, _d in self.published]


class RaisingPublisher:
    """A bus that is down in the least forgiving way: every publish explodes."""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def publish(self, *, event_type, subject, data) -> None:
        self.attempts.append(event_type)
        raise ConnectionError("bus unreachable")


@pytest.fixture(autouse=True)
def _skip_slidev_build(monkeypatch: pytest.MonkeyPatch) -> None:
    from engine.adapters.outbound.slidev.slidev_builder import SlidevBuilder

    monkeypatch.setattr(SlidevBuilder, "build", lambda self, *a, **kw: True)


def _tree(root: Path) -> dict[str, object]:
    """Compare all content, normalizing workbook creation/modification times."""
    result: dict[str, object] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        key = p.relative_to(root).as_posix()
        if p.suffix != ".xlsx":
            result[key] = p.read_bytes()
            continue
        with ZipFile(p) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        core = ElementTree.fromstring(parts["docProps/core.xml"])
        for element in core:
            if element.tag in {
                "{http://purl.org/dc/terms/}created",
                "{http://purl.org/dc/terms/}modified",
            }:
                element.text = "normalized"
        parts["docProps/core.xml"] = ElementTree.tostring(core)
        result[key] = parts
    return result


# Each act: scaffolds what it needs, performs the act, returns something comparable.
def _scaffold(c: Container, root: Path):
    return c.scaffold_project().execute(root, "acme").name


def _write(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    c.write_project_file().execute(root / "acme", "data/notes.tsv", "a\tb\n")
    return (root / "acme" / "data/notes.tsv").read_text(encoding="utf-8")


def _append_rows(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    c.write_project_file().execute(root / "acme", "data/notes.tsv", "Note ID\tText\nN-1\ta\n")
    c.append_project_rows().execute(
        root / "acme", "data/notes.tsv", [{"Note ID": "N-2", "Text": "b"}]
    )
    return (root / "acme" / "data/notes.tsv").read_text(encoding="utf-8")


def _replace_row(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    c.write_project_file().execute(root / "acme", "data/notes.tsv", "Note ID\tText\nN-1\ta\n")
    c.replace_project_row().execute(
        root / "acme", "data/notes.tsv", "N-1", {"Note ID": "N-1", "Text": "b"}
    )
    return (root / "acme" / "data/notes.tsv").read_text(encoding="utf-8")


def _delete_file(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    c.write_project_file().execute(root / "acme", "data/notes.tsv", "a\tb\n")
    c.delete_project_file().execute(root / "acme", "data/notes.tsv")
    return (root / "acme" / "data/notes.tsv").exists()


def _generate(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    result = c.generate_all().execute(root / "acme", pipelines=[Pipeline.ROADMAP, Pipeline.EXCEL])
    return sorted((p.value, ok) for p, ok in result.outcomes.items())


def _rename(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    return c.rename_project().execute(root, "acme", new_slug="acme-two", new_name="Acme Two").name


def _archive(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    return c.archive_project().execute(root, "acme").name


def _unarchive(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    c.archive_project().execute(root, "acme")
    return c.unarchive_project().execute(root, "acme").name


def _delete(c: Container, root: Path):
    c.scaffold_project().execute(root, "acme")
    c.delete_project().execute(root, "acme")
    return (root / "acme").exists()


_ACTS = [
    pytest.param(_scaffold, [PROJECT_SCAFFOLDED], id="scaffold"),
    pytest.param(_write, [PROJECT_SCAFFOLDED, FILE_WRITTEN], id="write-file"),
    pytest.param(_append_rows, [PROJECT_SCAFFOLDED, FILE_WRITTEN, FILE_WRITTEN], id="append-rows"),
    pytest.param(_replace_row, [PROJECT_SCAFFOLDED, FILE_WRITTEN, FILE_WRITTEN], id="replace-row"),
    pytest.param(_delete_file, [PROJECT_SCAFFOLDED, FILE_WRITTEN, FILE_DELETED], id="delete-file"),
    pytest.param(_generate, [PROJECT_SCAFFOLDED, ARTIFACT_GENERATED, ARTIFACT_GENERATED], id="generate"),
    pytest.param(_rename, [PROJECT_SCAFFOLDED, PROJECT_RENAMED], id="rename"),
    pytest.param(_archive, [PROJECT_SCAFFOLDED, PROJECT_ARCHIVED], id="archive"),
    pytest.param(_unarchive, [PROJECT_SCAFFOLDED, PROJECT_ARCHIVED, PROJECT_UNARCHIVED], id="unarchive"),
    pytest.param(_delete, [PROJECT_SCAFFOLDED, PROJECT_DELETED], id="delete"),
]


@intent("INT-ESTIMATEKIT-016")
@pytest.mark.parametrize(("act", "facts"), _ACTS)
def test_every_act_is_identical_with_the_bus_down(tmp_path: Path, caplog, act, facts) -> None:
    up_root, down_root = tmp_path / "up", tmp_path / "down"
    up_root.mkdir()
    down_root.mkdir()

    up = RecordingPublisher()
    result_up = act(Container(projects_root=up_root, events=up), up_root)
    assert up.types == facts
    for _t, subject, data in up.published:
        assert subject
        assert json.dumps(data)
        assert "numbers" not in data and "content" not in data  # pointers, never the data

    down = RaisingPublisher()
    with caplog.at_level(logging.WARNING, logger="engine"):
        result_down = act(Container(projects_root=down_root, events=down), down_root)
    assert down.attempts == facts, "the act must still attempt each publish"
    assert result_down == result_up
    # Identical file content, with workbook clock metadata normalized.
    assert _tree(up_root) == _tree(down_root)
    for fact in facts:
        assert any(fact in r.getMessage() for r in caplog.records), f"a dropped {fact} must be logged"


class _Runner:
    def __init__(self, passed: bool) -> None:
        self._passed = passed

    def run(self, project_path: Path) -> AuditReport:
        return AuditReport(
            checks=[],
            passed_count=3,
            failed_count=0 if self._passed else 2,
            skipped_count=1,
            passed=self._passed,
            duration_ms=5,
        )


class _Suggestions:
    def analyze(self, project_path: Path):
        return []


@intent("INT-ESTIMATEKIT-016")
def test_the_audit_verdict_is_stated_and_the_report_is_identical_with_the_bus_down(tmp_path: Path, caplog):
    """The audit verdict is the fact a routine watches; the findings stay in the
    report a caller fetches."""
    (tmp_path / "project.yaml").write_text("name: acme\n", encoding="utf-8")
    up = RecordingPublisher()
    report_up = RunAudit(_Runner(False), _Suggestions(), events=up).execute(tmp_path)
    assert up.types == [AUDIT_COMPLETED]
    data = up.published[0][2]
    assert data["verdict"] == "fail" and data["failed"] == 2 and "checks" not in data

    down = RaisingPublisher()
    with caplog.at_level(logging.WARNING, logger="engine"):
        report_down = RunAudit(_Runner(False), _Suggestions(), events=down).execute(tmp_path)
    assert down.attempts == [AUDIT_COMPLETED]
    assert report_down == report_up
    assert any(AUDIT_COMPLETED in r.getMessage() for r in caplog.records)


@intent("INT-ESTIMATEKIT-016")
def test_state_fact_never_raises_and_no_publisher_states_nothing(caplog):
    with caplog.at_level(logging.WARNING, logger="engine"):
        state_fact(RaisingPublisher(), event_type=PROJECT_SCAFFOLDED, subject="acme", data={})
    assert any(PROJECT_SCAFFOLDED in r.getMessage() for r in caplog.records)
    state_fact(None, event_type=PROJECT_SCAFFOLDED, subject="acme", data={})


@intent("INT-ESTIMATEKIT-016")
def test_the_envelope_is_a_cloudevent_carrying_pointers_not_payloads():
    event = json.loads(cloud_event(event_type=AUDIT_COMPLETED, subject="acme", data={"project": "acme"}))
    assert event["specversion"] == "1.0"
    assert event["type"] == AUDIT_COMPLETED
    assert event["subject"] == "acme"
    assert event["source"] == SOURCE
    assert event["datacontenttype"] == "application/json"
    assert event["id"] and event["time"]
    assert json.loads(cloud_event(event_type=AUDIT_COMPLETED, subject="acme", data={}))["id"] != event["id"]
    with pytest.raises(TypeError):
        cloud_event(event_type=AUDIT_COMPLETED, subject="acme", data={"report": object()})
    LoggingEventPublisher().publish(event_type=AUDIT_COMPLETED, subject="acme", data={"report": object()})


_EVENTS_PAGE = Path(__file__).resolve().parents[3] / "docs/src/content/docs/architecture/events.md"


@intent("INT-ESTIMATEKIT-016")
def test_the_events_page_states_exactly_the_types_the_engine_emits():
    """REF-Events section 3: each owner states its own types on its own page, held
    against the publisher by its own tests."""
    emitted = {
        value
        for name, value in vars(vocabulary).items()
        if name.isupper() and isinstance(value, str) and value.startswith("com.foundry.")
    }
    assert emitted
    assert {v.split(".")[2] for v in emitted} == {"estimation"}
    stated = set(re.findall(r"^\| `(com\.foundry\.[a-z.]+)` \|", _EVENTS_PAGE.read_text(encoding="utf-8"), flags=re.M))
    assert stated == emitted, (
        f"page states {sorted(stated - emitted)} the engine never emits; "
        f"engine emits {sorted(emitted - stated)} the page never states"
    )
