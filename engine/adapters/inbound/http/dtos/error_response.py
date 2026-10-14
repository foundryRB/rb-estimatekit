"""Response DTO for error responses."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error envelope for all API error responses."""

    error: str
    detail: str
