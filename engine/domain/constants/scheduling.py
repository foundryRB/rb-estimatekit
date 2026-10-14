"""Scheduling constants."""

from __future__ import annotations

DAYS_PER_MONTH: int = 20  # working days per scheduling month

DEV_STREAM_PREFIX: str = "2.Dev"
"""Stream-name prefix marking development streams in the numbered-stream
naming convention the scaffold uses ('0.Lead', '1.Design', '2.Dev', '3.Test').
The build scheduler reads build capacity from these streams when any stream
uses the prefix, and from all streams otherwise."""

QA_STREAM_KEYS: tuple[str, ...] = ("test", "qa", "quality")
"""Substrings marking a test stream: a stream whose name contains any of them,
ignoring case, is one ('3.Test', '3.Quality', 'QA'). The audit's QA window
check reads its effort and capacity from these streams, and the delivery-risk
analyzer counts their effort as QA."""


def is_qa_stream(stream: str) -> bool:
    """Whether *stream* names a test stream, by ``QA_STREAM_KEYS``."""
    name = stream.lower()
    return any(key in name for key in QA_STREAM_KEYS)
