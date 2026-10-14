"""Domain model — aggregates, entities, and value objects."""

from engine.domain.exceptions import (  # noqa: F401 — re-export
    AppError,
    ConfigurationError,
    DataFileNotFoundError,
    DataFileParseError,
    GenerationError,
    ProjectLoadError,
    ProjectNotFoundError,
    SchedulingError,
    TemplateNotFoundError,
)

# Aggregates
from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.aggregates.project import Project

# Entities
from engine.domain.model.entities.assumption import Assumption
from engine.domain.model.entities.build_activity import BuildActivity
from engine.domain.model.entities.component import Component
from engine.domain.model.entities.executive_summary_data import ExecutiveSummaryData
from engine.domain.model.entities.guideline import Guideline
from engine.domain.model.entities.project_activity import ProjectActivity
from engine.domain.model.entities.requirement import Requirement
from engine.domain.model.entities.slide_note import SlideNote

# Value Objects
from engine.domain.model.value_objects.branding import BrandConfig
from engine.domain.model.value_objects.category import Category
from engine.domain.model.value_objects.cell_marker import CellMarker
from engine.domain.model.value_objects.confidence import Confidence
from engine.domain.model.value_objects.config import ProjectConfig
from engine.domain.model.value_objects.generation_result import GenerationResult
from engine.domain.model.value_objects.group_effort import GroupEffort
from engine.domain.model.value_objects.group_schedule import GroupSchedule
from engine.domain.model.value_objects.impact import Impact
from engine.domain.model.value_objects.phase_config import PhaseConfig
from engine.domain.model.value_objects.phase_effort import PhaseEffort
from engine.domain.model.value_objects.phase_id import PhaseId
from engine.domain.model.value_objects.phase_roadmap import PhaseRoadmap
from engine.domain.model.value_objects.pipeline import Pipeline
from engine.domain.model.value_objects.project_summary import ProjectSummary
from engine.domain.model.value_objects.resource_plan import ResourcePlan
from engine.domain.model.value_objects.roadmap_view import RoadmapView
from engine.domain.model.value_objects.view_row import ViewRow
from engine.domain.model.value_objects.vrom_entry import VromEntry

__all__ = [
    # Aggregates
    "Phase",
    "Project",
    # Entities
    "Assumption",
    "BuildActivity",
    "Component",
    "ExecutiveSummaryData",
    "Guideline",
    "ProjectActivity",
    "Requirement",
    "SlideNote",
    # Value Objects
    "BrandConfig",
    "Category",
    "CellMarker",
    "Confidence",
    "GenerationResult",
    "GroupEffort",
    "GroupSchedule",
    "Impact",
    "PhaseConfig",
    "PhaseEffort",
    "PhaseId",
    "PhaseRoadmap",
    "Pipeline",
    "ProjectConfig",
    "ProjectSummary",
    "ResourcePlan",
    "RoadmapView",
    "ViewRow",
    "VromEntry",
    # Exceptions
    "ConfigurationError",
    "DataFileNotFoundError",
    "DataFileParseError",
    "AppError",
    "GenerationError",
    "ProjectLoadError",
    "ProjectNotFoundError",
    "SchedulingError",
    "TemplateNotFoundError",
]
