"""FastAPI exception handler — registers a single handler for domain errors."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from engine.adapters.inbound.http.mappers.exception_mapper import DEFAULT_STATUS, STATUS_MAP
from engine.domain.exceptions import AppError


def register_exception_handler(app: FastAPI) -> None:
    """Attach a single generic exception handler for all domain errors."""

    @app.exception_handler(AppError)
    async def _handle_engine_error(
        _request: Request, exc: AppError,
    ) -> JSONResponse:
        status = STATUS_MAP.get(type(exc), DEFAULT_STATUS)
        return JSONResponse(
            status_code=status,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
            },
        )

