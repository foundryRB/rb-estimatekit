"""TSV column name constants and related mappings."""

from __future__ import annotations

COL_PHASE_ID = "Phase ID"
COL_PHASE = "Phase"
COL_NAME = "Name"
COL_DESCRIPTION = "Description"
COL_CATEGORY = "Category"
COL_REQ_ID = "Req ID"
COL_REQ_IDS = "Req IDs"
COL_EFFORT_MD = "Effort (MD)"
COL_STREAM = "Stream"
COL_PROFILE = "Profile"
COL_RATE_DAY = "Rate Day"
COL_ACTIVITY_ID = "Activity ID"
COL_ACTIVITY = "Activity"
COL_ACTIVITY_GROUP = "Activity Group"
COL_GROUP = "Group"
COL_ASSUMPTION_ID = "Assumption ID"
COL_ASSUMPTION = "Assumption"
COL_SHORT_TITLE = "Short Title"
COL_CONFIDENCE = "Confidence"
COL_IMPACT = "Impact"
COL_PARAMETER = "Parameter"
COL_VALUE = "Value"
COL_INTEGRATION_TYPE = "Integration Type"
COL_EXAMPLES = "Examples"
COL_NOTES = "Notes"
COL_LAYER = "Layer"
COL_TECHNOLOGY = "Technology"
COL_COMPONENT = "Component"
COL_GUIDELINE_ID = "Guideline ID"
COL_ID = "ID"
COL_GUIDELINE = "Guideline"
COL_PHASE_IDS = "Phase IDs"
COL_SECTION = "Section"
COL_KEY = "Key"
COL_SLIDE = "Slide"
COL_POSITION = "Position"
COL_TEXT = "Text"

RESOURCE_SKIP_COLS = frozenset({COL_STREAM, COL_PROFILE, COL_RATE_DAY})
"""Non-month columns to skip when parsing resource TSVs."""

CONFIG_PARAM_MAP: dict[str, str] = {
    "Design Lead": "design_lead_days",
    "Testing Lag": "lag_pct",
    "SIT Duration": "sit_days",
    "UAT Duration": "uat_days",
}
"""Maps TSV parameter names to PhaseConfig field names."""
