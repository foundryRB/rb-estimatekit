"""The facts this engine states on the platform event bus, and the one way to state one.

REF-Events gives each domain exactly one owner, and this engine owns
``estimation`` by its grant. The constants below are its whole vocabulary; the
docs page ``architecture/events.md`` states the same rows for consumers, and a
test holds the two equal so neither can drift (REF-Events section 3: each owner
states its own types, held by its own tests). A type is never composed at a
call site. No project data enters an event: the engine stays the store, and a
reader fetches by slug.

``state_fact`` is where the one-way rule is enforced for every caller at once.
A publisher is contractually forbidden from raising, but a caller that trusted
that contract and was wrong would fail the act it had already committed (an
audit whose verdict is lost because a broker is down), which is the single
failure REF-Events section 6 exists to prevent. So the guarantee is made true
here rather than assumed.
"""

from __future__ import annotations

from engine.application.ports.outbound.event_publisher import EventPublisher
from engine.logging import get_logger

__all__ = [
    "ARTIFACT_GENERATED",
    "AUDIT_COMPLETED",
    "FILE_DELETED",
    "FILE_WRITTEN",
    "PROJECT_ARCHIVED",
    "PROJECT_DELETED",
    "PROJECT_RENAMED",
    "PROJECT_SCAFFOLDED",
    "PROJECT_UNARCHIVED",
    "state_fact",
]

logger = get_logger(__name__)

# The estimation domain: the projects this engine holds and the artifacts it cuts.
PROJECT_SCAFFOLDED = "com.foundry.estimation.project.scaffolded"
FILE_WRITTEN = "com.foundry.estimation.file.written"
FILE_DELETED = "com.foundry.estimation.file.deleted"
AUDIT_COMPLETED = "com.foundry.estimation.audit.completed"
ARTIFACT_GENERATED = "com.foundry.estimation.artifact.generated"
PROJECT_RENAMED = "com.foundry.estimation.project.renamed"
PROJECT_ARCHIVED = "com.foundry.estimation.project.archived"
PROJECT_UNARCHIVED = "com.foundry.estimation.project.unarchived"
PROJECT_DELETED = "com.foundry.estimation.project.deleted"


def state_fact(
    publisher: EventPublisher | None,
    *,
    event_type: str,
    subject: str,
    data: dict[str, object],
) -> None:
    """Publish a fact, and let nothing about it reach the caller.

    Every failure mode ends the same way: dropped, logged at warning, and the
    act that caused it completes with the outcome it already had. No publisher
    wired (an engine with no bus grant, or the CLI) states nothing.
    """
    if publisher is None:
        return
    try:
        publisher.publish(event_type=event_type, subject=subject, data=data)
    except Exception as exc:  # noqa: BLE001 - a publish never fails its cause
        logger.warning("dropped event %s for %s: %s", event_type, subject, exc)
