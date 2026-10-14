"""Mapper: domain exceptions to HTTP status codes."""

from __future__ import annotations

from engine.domain.exceptions import (
    AppError,
    ConfigurationError,
    DataFileNotFoundError,
    DataFileParseError,
    DiagramRenderError,
    GenerationError,
    InvalidPathError,
    InvalidPhaseIdError,
    InvalidRateError,
    InvalidRenameError,
    InvalidRowError,
    InvalidSlugError,
    OutputFileNotFoundError,
    PhaseAlreadyExistsError,
    PhaseInputMissingError,
    PhaseNotFoundError,
    PhaseRequiredError,
    ProjectAlreadyExistsError,
    ProjectLoadError,
    ProjectNotFoundError,
    SchedulingError,
    TemplateNotFoundError,
)

STATUS_MAP: dict[type[AppError], int] = {
    InvalidPathError: 400,
    InvalidPhaseIdError: 400,
    InvalidRenameError: 400,
    InvalidSlugError: 400,
    ProjectNotFoundError: 404,
    DataFileNotFoundError: 404,
    OutputFileNotFoundError: 404,
    TemplateNotFoundError: 404,
    PhaseAlreadyExistsError: 409,
    ProjectAlreadyExistsError: 409,
    DataFileParseError: 422,
    DiagramRenderError: 422,
    ConfigurationError: 422,
    InvalidRateError: 422,
    InvalidRowError: 422,
    PhaseInputMissingError: 422,
    PhaseNotFoundError: 422,
    PhaseRequiredError: 422,
    ProjectLoadError: 422,
    GenerationError: 500,
    SchedulingError: 500,
}

DEFAULT_STATUS = 500
