"""Domain exceptions — all engine errors inherit from AppError.

Import any specific exception directly::

    from engine.domain.exceptions import ProjectNotFoundError

Or import the base for catch-all handling::

    from engine.domain.exceptions import AppError
"""

from engine.domain.exceptions.app_error import AppError
from engine.domain.exceptions.configuration_error import ConfigurationError
from engine.domain.exceptions.data_file_not_found_error import DataFileNotFoundError
from engine.domain.exceptions.data_file_parse_error import DataFileParseError
from engine.domain.exceptions.diagram_render_error import DiagramRenderError
from engine.domain.exceptions.generation_error import GenerationError
from engine.domain.exceptions.invalid_path_error import InvalidPathError
from engine.domain.exceptions.invalid_phase_id_error import InvalidPhaseIdError
from engine.domain.exceptions.invalid_rate_error import InvalidRateError
from engine.domain.exceptions.invalid_rename_error import InvalidRenameError
from engine.domain.exceptions.invalid_row_error import InvalidRowError
from engine.domain.exceptions.invalid_slug_error import InvalidSlugError
from engine.domain.exceptions.output_file_not_found_error import OutputFileNotFoundError
from engine.domain.exceptions.phase_already_exists_error import PhaseAlreadyExistsError
from engine.domain.exceptions.phase_input_missing_error import PhaseInputMissingError
from engine.domain.exceptions.phase_not_found_error import PhaseNotFoundError
from engine.domain.exceptions.phase_required_error import PhaseRequiredError
from engine.domain.exceptions.project_already_exists_error import ProjectAlreadyExistsError
from engine.domain.exceptions.project_load_error import ProjectLoadError
from engine.domain.exceptions.project_not_found_error import ProjectNotFoundError
from engine.domain.exceptions.scheduling_error import SchedulingError
from engine.domain.exceptions.template_not_found_error import TemplateNotFoundError

__all__ = [
    "ConfigurationError",
    "DataFileNotFoundError",
    "DataFileParseError",
    "AppError",
    "DiagramRenderError",
    "GenerationError",
    "InvalidPathError",
    "InvalidPhaseIdError",
    "InvalidRateError",
    "InvalidRenameError",
    "InvalidRowError",
    "InvalidSlugError",
    "OutputFileNotFoundError",
    "PhaseAlreadyExistsError",
    "PhaseInputMissingError",
    "PhaseNotFoundError",
    "PhaseRequiredError",
    "ProjectAlreadyExistsError",
    "ProjectLoadError",
    "ProjectNotFoundError",
    "SchedulingError",
    "TemplateNotFoundError",
]
