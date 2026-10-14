"""Label parsing helpers for roadmap Gantt slides.

Phase detection works off the project's *actual* phase IDs, passed in by the
caller — never a fixed registry — so a project with any phase set (four, five,
or more) parses correctly. Prefixes are matched longest-first, so a ``P2`` id
never swallows a ``P2A-M1`` label.
"""

from __future__ import annotations

from collections.abc import Iterable

__all__ = [
    "detect_phase_from_label",
    "stream_short",
    "strip_month_prefix",
    "strip_row_phase_prefix",
]


def _ordered(phase_ids: Iterable[str]) -> list[str]:
    """Phase ids sorted longest-first, so ``P2A`` is tried before ``P2``."""
    return sorted(phase_ids, key=len, reverse=True)


def stream_short(stream: str) -> str:
    """Strip ``0.`` numeric prefix from stream names (e.g. '2.Dev' -> 'Dev')."""
    if len(stream) > 2 and stream[1] == ".":
        return stream[2:]
    return stream


def detect_phase_from_label(label: str, phase_ids: Iterable[str]) -> str:
    """Detect phase from a prefixed month label like ``P1-M3``.

    Testing-tail overflow labels (``X-M16``) are left as unknown.
    """
    for pid in _ordered(phase_ids):
        if label.startswith(pid + "-") or label.startswith(pid + " "):
            return pid
    # Bare "M1", "M2" etc. — no phase prefix
    return ""


def strip_month_prefix(label: str, phase_ids: Iterable[str]) -> str:
    """Strip known phase prefix from month label (``P1-M3`` -> ``M3``)."""
    for pid in _ordered(phase_ids):
        if label.startswith(pid + "-"):
            return label[len(pid) + 1 :]
    if label.startswith("X-"):
        return "+1"
    return label


def strip_row_phase_prefix(label: str, phase_ids: Iterable[str]) -> str:
    """Strip phase prefix on all-phases row labels (``P1: Design Lead`` -> ``Design Lead``)."""
    for pid in _ordered(phase_ids):
        if label.startswith(pid + ": "):
            return label[len(pid) + 2 :]
    return label
