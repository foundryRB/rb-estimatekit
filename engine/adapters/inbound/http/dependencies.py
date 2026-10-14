"""Container singleton for FastAPI dependency injection."""

from __future__ import annotations

from functools import lru_cache

from engine.container import Container

__all__ = ["get_container"]


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Return the shared Container singleton."""
    return Container()
