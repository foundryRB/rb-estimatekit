"""Project lifecycle marker filenames.

Markers are empty files inside a project directory that carry lifecycle
state, mirroring how ``project.yaml``'s presence marks a valid project.
"""

from __future__ import annotations

__all__ = ["ARCHIVED_MARKER"]

ARCHIVED_MARKER = ".archived"
"""Present in a project directory when the project is archived."""
