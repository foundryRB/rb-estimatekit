"""Mapper: domain exceptions to CLI exit codes."""

from __future__ import annotations

from engine.domain.exceptions import (
    AppError,
    ConfigurationError,
    DataFileNotFoundError,
    DataFileParseError,
    GenerationError,
    InvalidPhaseIdError,
    InvalidRateError,
    PhaseAlreadyExistsError,
    PhaseInputMissingError,
    PhaseNotFoundError,
    PhaseRequiredError,
    ProjectLoadError,
    ProjectNotFoundError,
    SchedulingError,
    TemplateNotFoundError,
)

EXIT_CODE_MAP: dict[type[AppError], int] = {
    ProjectNotFoundError: 2,
    DataFileNotFoundError: 2,
    TemplateNotFoundError: 2,
    DataFileParseError: 3,
    ConfigurationError: 3,
    InvalidPhaseIdError: 3,
    InvalidRateError: 3,
    PhaseAlreadyExistsError: 3,
    PhaseInputMissingError: 3,
    PhaseNotFoundError: 3,
    PhaseRequiredError: 3,
    ProjectLoadError: 3,
    GenerationError: 4,
    SchedulingError: 4,
}

DEFAULT_EXIT_CODE = 1
