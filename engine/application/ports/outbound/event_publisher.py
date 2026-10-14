"""Port: event publisher — state a fact about this engine's own domain on the bus."""

from __future__ import annotations

from typing import Protocol

__all__ = ["EventPublisher"]


class EventPublisher(Protocol):
    """Publish one past-tense fact, and never make the caller wait on it.

    The contract is REF-Events. Two of its rules shape this port:

    - **Publishing is one-way.** An implementation MUST NOT raise, block past a
      short bound, or otherwise change the outcome of the act that caused the
      publish. A publish that cannot be delivered is dropped and logged. No
      audit or generation outcome depends on a broker.
    - **The envelope is the contract, not the transport.** Callers state the
      fact (``event_type``, ``subject``, ``data``); the adapter shapes the
      CloudEvents envelope and chooses how it travels.

    ``event_type`` is one row of this engine's own vocabulary
    (``engine.application.events``), never composed at the call site.
    ``subject`` is the project slug. ``data`` carries identity and pointers,
    never the project's numbers.
    """

    def publish(self, *, event_type: str, subject: str, data: dict[str, object]) -> None:
        """State the fact. Never tells the caller whether it was delivered."""
        ...
